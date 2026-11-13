"""Authorized stage driver. All product effects execute through the existing Temporal workflow."""
import argparse,asyncio,fcntl,hashlib,json,logging,os,sys
from pathlib import Path
from uuid import UUID,uuid4,uuid5
sys.path.insert(0,str(Path.cwd()))
os.umask(0o077)
os.environ['PATH']=str(Path.cwd()/'.local/tools/motion-lab/bin')+os.pathsep+os.environ['PATH']
from execution_config import proposed,HERE,BUNDLE,PAYLOAD_SHA,CAP,RESERVE
from sqlalchemy import text
from temporalio.client import Client
from temporalio.worker import Worker
from app.db.session import Database
from app.adapters.motion_ai import request_bytes
from app.schemas.motion_production import MotionRequest
from app.schemas.motion_preparation import MotionCheckpointDecision
from app.schemas.motion_storyboards import StoryboardDecision
from app.services.motion_checkpoints import MotionCheckpoints
from app.services.motion_storyboards import MotionStoryboards
from app.services.motion_plan_revision import MotionPlanRevision
from app.schemas.motion_plan_revision import MotionDirectionObservation
from app.services.motion_render_recovery import MotionRenderRecovery
from app.services.motion_review_recovery import MotionReviewRecovery
from app.adapters.motion_html_renderer import IsolatedMotionRenderer
RENDERER_IMAGE="sha256:fbdc637cfc6c64034f7328dc096c586464030628c23c743a6316e77a90bd6e79"
from app.services.motion_runtime import build_motion_runner
from app.services.outbox import dispatch_once
from app.workflows.motion_activities import MotionActivities
from app.workflows.motion_production import MotionProductionWorkflow
from scripts.evals.motion_external_export import verify_export
logging.getLogger('httpx').setLevel(logging.CRITICAL)
logging.getLogger('temporalio.activity').setLevel(logging.CRITICAL)
DISPATCHABLE=text("""SELECT id FROM outbox_events WHERE event_type IN
('business.created','brand_kit.changed','reference.search_requested','reference.selection_confirmed',
'motion.requested','motion.storyboard_approved','motion.storyboard_recapture_requested','motion.plan_approved','motion.render_approved')
AND ((state='pending' AND available_at<=clock_timestamp()) OR (state='leased' AND lease_until<=clock_timestamp()))""")

def save(path,value):
    with os.fdopen(os.open(path,os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600),'w') as f:
        json.dump(value,f,ensure_ascii=False,indent=2,default=str,allow_nan=False)

def normalized(value):
    value=json.loads(request_bytes(value))
    for message in value['input']:
        for block in message['content']:
            if block['type']=='input_text':
                try: parsed=json.loads(block['text'])
                except ValueError: continue
                block['text']=json.dumps(parsed,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False)
    return request_bytes(value)

class GuardedProvider:
    provider='openai'
    model='gpt-6.1-sol'
    def __init__(self,delegate,root):
        self.delegate,self.root=delegate,root
        revision=uuid5(root,'plan-revision:1')
        self.operations=(root,revision,uuid5(revision,'admission-recovery:1'))
        self.journal=HERE/'provider-journal';self.journal.mkdir(exist_ok=True)
    def build_request(self,job):
        stages=['generate:plan:0','generate:0',*[f'review:{n}' for n in range(3)],'correct:1','correct:2']
        assert job.operation_id in {uuid5(op,s) for op in self.operations for s in stages},'UNAUTHORIZED_OPERATION'
        payload=self.delegate.build_request(job)
        if job.operation_id==uuid5(self.root,'generate:plan:0'):
            expected=json.loads((BUNDLE/'generation-request.json').read_bytes())
            assert normalized(payload)==normalized(expected),'INITIAL_INPUT_CHANGED'
        return payload
    async def wait_for_ci(self):
        return
    async def count_input_tokens(self,job,payload):
        await self.wait_for_ci()
        assert request_bytes(payload)==request_bytes(self.build_request(job))
        save(self.journal/(str(job.operation_id)+'-request.json'),payload)
        count=await self.delegate.count_input_tokens(job,payload)
        save(self.journal/(str(job.operation_id)+'-count.json'),{'input_tokens':count})
        return count
    async def submit(self,job,payload):
        await self.wait_for_ci()
        assert len(list(self.journal.glob('*-submission.json')))<10,'SUBMISSION_CAP_REACHED'
        saved=json.loads((self.journal/(str(job.operation_id)+'-request.json')).read_bytes())
        assert request_bytes(payload)==request_bytes(saved),'COUNTED_INPUT_CHANGED'
        save(self.journal/(str(job.operation_id)+'-submission.json'),{
            'operation_id':job.operation_id,'kind':job.kind,'reserved_usd_micros':RESERVE,
            'payload_sha256':hashlib.sha256(request_bytes(payload)).hexdigest()})
        result=await self.delegate.submit(job,payload)
        save(self.journal/(str(job.operation_id)+'-result.json'),{
            'estimated_usd_micros':result.estimated_usd_micros,'usage':result.usage})
        return result

async def main(args):
    auth=json.loads((HERE/'owner-authorization.json').read_bytes())
    assert auth['approved'] is True and auth['maximum_usd_micros']==CAP and auth['maximum_submissions']==10
    assert auth['initial_payload_sha256']==PAYLOAD_SHA
    assert hashlib.sha256((BUNDLE/'generation-request.json').read_bytes()).hexdigest()==PAYLOAD_SHA
    assert hashlib.sha256((HERE/'budget-baseline.json').read_bytes()).hexdigest()==auth['budget_baseline_sha256']
    verify_export(BUNDLE)
    cfg,ids=proposed()
    if args.revision: cfg=cfg.model_copy(update={"motion_renderer_image":RENDERER_IMAGE})
    assert not cfg.reference_learning_ready() and not cfg.reference_geocoding_ready()
    (HERE/'native-scratch').mkdir(exist_ok=True)
    body=MotionRequest.model_validate_json((BUNDLE/'request.json').read_bytes())
    root=body.operation_id
    assert str(root)==auth['operation_id']
    operation=uuid5(root,'plan-revision:1') if args.revision else root
    if args.recovered:
        assert args.revision
        operation=uuid5(operation,'admission-recovery:1')
    request=uuid5(operation,f"motion-request:{ids['tenant']}:{ids['business']}")
    run=HERE/('native-'+('revision-' if args.revision else '')+('recovered-' if args.recovered else '')+args.action)
    run.mkdir(exist_ok=False)
    db,costs,relay=Database(cfg),Database(cfg,correlator=True),Database(cfg,relay=True)
    try:
        async with db.sessions() as s: assert await s.scalar(text('SELECT version_num FROM alembic_version'))=='0118_motion_checkpoint_events'
        async with relay.sessions() as s: assert not (await s.execute(DISPATCHABLE)).scalars().all(),'UNRELATED_DISPATCHABLE_EVENTS'
        client=await Client.connect(cfg.temporal_address)
        runner=build_motion_runner(cfg,db,costs)
        if args.action in ('recover-render','recover-review'):
            proof=json.loads((HERE/"renderer-audio-proof/receipt.json").read_bytes())
            assert proof["image"]==RENDERER_IMAGE and len(proof["diagnostics"]["frame_fingerprints"])==120
            runner.renderer=IsolatedMotionRenderer(image=RENDERER_IMAGE,docker_executable=Path(cfg.motion_renderer_docker_executable),docker_socket=Path(cfg.motion_renderer_docker_socket),scratch_directory=HERE/"native-scratch")
        custom_event=None
        runner.provider=GuardedProvider(runner.provider,root)
        checks=MotionCheckpoints(runner.requests,runner.store)
        boards=MotionStoryboards(runner.requests,runner.store)
        async with Worker(client,task_queue=cfg.temporal_task_queue,workflows=[MotionProductionWorkflow],activities=[MotionActivities(runner).run]):
            if args.action=='start':
                assert not args.revision
                admitted=await runner.requests.create(ids['tenant'],ids['business'],ids['actor'],body)
                assert admitted.id==request
                save(run/'admission.json',admitted.model_dump(mode='json'))
                event_kind,prefix='motion.requested','motion-production'
            elif args.action=='recover-admission':
                assert args.revision and args.recovered
                refused_operation=uuid5(root,'plan-revision:1')
                refused_request=uuid5(refused_operation,f"motion-request:{ids['tenant']}:{ids['business']}")
                admitted=await runner.requests.recover_admission(ids['tenant'],ids['business'],ids['actor'],refused_request)
                assert admitted.id==request
                save(run/'admission.json',admitted.model_dump(mode='json'))
                event_kind,prefix='motion.requested','motion-production'
            elif args.action=='replan':
                assert args.revision
                parent=uuid5(root,f"motion-request:{ids['tenant']}:{ids['business']}")
                observation=MotionDirectionObservation.model_validate_json(Path(args.observation_path).read_bytes()) if args.observation_path else None
                admitted=await MotionPlanRevision(runner.requests).create(ids['tenant'],ids['business'],ids['actor'],parent,observation)
                if observation: save(run/'operator-observation.json',observation.model_dump(mode='json'))
                assert admitted.id==request
                save(run/'admission.json',admitted.model_dump(mode='json'))
                event_kind,prefix='motion.requested','motion-production'
            elif args.action=='recover-review':
                assert not args.revision and args.sha
                custom_event=await MotionReviewRecovery(runner).request(ids['tenant'],ids['business'],ids['actor'],request,args.sha)
                event_kind,prefix='motion.storyboard_approved','motion-storyboard-approved'
                save(run/'recovery.json',{'event_id':custom_event,'image':RENDERER_IMAGE,'mp4_sha256':args.sha,'render_replayed':False})
            elif args.action=='recover-render':
                assert not args.revision and args.sha
                custom_event=await MotionRenderRecovery(runner).request(ids['tenant'],ids['business'],ids['actor'],request,args.sha,RENDERER_IMAGE)
                event_kind,prefix='motion.storyboard_approved','motion-storyboard-approved'
                save(run/'recovery.json',{'event_id':custom_event,'image':RENDERER_IMAGE,'board_sha256':args.sha,'paid_generation_replayed':False})
            elif args.action in ('plan','render'):
                view=await checks.present(ids['tenant'],ids['business'],ids['actor'],request,args.action)
                assert args.sha and view['content_sha256']==args.sha and view['decision'] is None
                save(run/'reviewed-checkpoint.json',view)
                decision=MotionCheckpointDecision(operation_id=uuid5(operation,'quality-approve:'+args.action),
                    content_sha256=args.sha,decision='approve',note=args.note)
                save(run/'decision.json',decision.model_dump(mode='json'))
                await checks.decide(ids['tenant'],ids['business'],ids['actor'],request,args.action,decision)
                event_kind,prefix='motion.'+args.action+'_approved','motion-'+args.action+'-approved'
            else:
                _,board,payload=await boards.load(ids['tenant'],ids['business'],ids['actor'],request)
                assert args.sha and board['content_sha256']==args.sha and board['state']=='awaiting_approval'
                decision=StoryboardDecision(operation_id=uuid5(operation,'quality-approve:storyboard'),
                    version_id=board['version_id'],content_sha256=args.sha,decision='approve',feedback=args.note)
                save(run/'decision.json',decision.model_dump(mode='json'))
                await boards.decide(ids['tenant'],ids['business'],ids['actor'],request,decision)
                event_kind,prefix='motion.storyboard_approved','motion-storyboard-approved'
            event=custom_event or uuid5(operation,event_kind)
            async with relay.sessions() as s: assert set((await s.execute(DISPATCHABLE)).scalars())=={event}
            assert await dispatch_once(relay,client,cfg,uuid4())==1
            workflow=f"{prefix}/{ids['tenant']}/{event}"
            save(run/'workflow.json',{'workflow_id':workflow,'task_queue':cfg.temporal_task_queue,'request_id':request})
            state=await client.get_workflow_handle(workflow).result()
            if state in ('awaiting_plan','awaiting_render'):
                stage=state.removeprefix('awaiting_')
                view=await checks.present(ids['tenant'],ids['business'],ids['actor'],request,stage)
                save(run/'checkpoint.json',view)
                save(run/'artifact.json',view['packet']['artifact'])
            elif state=='awaiting_storyboard':
                _,board,payload=await boards.load(ids['tenant'],ids['business'],ids['actor'],request)
                save(run/'storyboard.json',boards.present(board,payload).model_dump(mode='json'))
                (run/'storyboard.html').write_text(await boards.gallery(ids['tenant'],ids['business'],ids['actor'],request))
                for n,f in enumerate(payload['frames']):
                    (run/f"frame-{n:02}-{f['at_ms']:05}.png").write_bytes(await boards.read_png(f))
            save(run/'completed.json',{'state':state,'request_id':request})
            print(json.dumps({'state':state,'request_id':str(request),'evidence':str(run)}),flush=True)
    finally:
        await db.close();await costs.close();await relay.close()

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action',choices=['start','plan','render','storyboard','replan','recover-render','recover-review','recover-admission'])
    parser.add_argument('--revision',action='store_true')
    parser.add_argument('--recovered',action='store_true')
    parser.add_argument('--sha')
    parser.add_argument('--observation-path')
    parser.add_argument('--note',default='Revisão do assistente no ciclo autorizado de US$ 12,50; não representa aceite visual final do titular.')
    args=parser.parse_args()
    with (HERE/'native-execution.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        try:asyncio.run(main(args))
        except Exception as exc:
            code=getattr(exc,'code',str(exc) if isinstance(exc,AssertionError) else type(exc).__name__)
            print(json.dumps({'event':'motion.native_step_failed','error_code':code}),flush=True)
            sys.exit(1)
