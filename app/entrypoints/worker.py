import asyncio

from temporalio.client import Client
from temporalio.worker import Worker

from app.adapters.audio_transcription import OpenAIAudioTranscriber
from app.adapters.editorial_ai import OpenAIEditorialProvider
from app.adapters.material_media import MaterialStore, MetaMediaClient
from app.core.config import Settings, get_settings
from app.core.logging import configure_logging
from app.db.session import Database
from app.services.audio_transcription import AudioTranscriptionService
from app.services.editorial_proposals import EditorialProposalService
from app.services.media_previews import MediaPreviewService
from app.services.visual_generation_runner import DatabaseVisualGenerationRunner
from app.services.whatsapp_processing import MaterialProcessor
from app.workflows.activities import FoundationActivities
from app.workflows.content_activities import ContentCandidateActivities
from app.workflows.content_candidate import ContentCandidateWorkflow
from app.workflows.content_publication import FakeContentPublicationWorkflow
from app.workflows.editorial_activities import EditorialActivities
from app.workflows.editorial_proposal import EditorialProposalWorkflow
from app.workflows.foundation import BrandKitChangedWorkflow, BusinessCreatedWorkflow
from app.workflows.media_activities import MediaPreviewActivities
from app.workflows.media_preview import StaticPreviewWorkflow
from app.workflows.visual_generation import VisualGenerationWorkflow
from app.workflows.visual_generation_activities import VisualGenerationActivities
from app.workflows.whatsapp_activities import WhatsAppMaterialActivities
from app.workflows.whatsapp_material import WhatsAppMaterialWorkflow


async def connect_temporal(settings: Settings) -> Client:
    return await Client.connect(
        settings.temporal_address,
        namespace=settings.temporal_namespace,
        tls=settings.temporal_tls,
        api_key=settings.temporal_api_key.get_secret_value() if settings.temporal_api_key else None,
    )


async def run_worker() -> None:
    configure_logging()
    settings = get_settings()
    database = Database(settings)
    material_database = Database(settings, correlator=True) if settings.correlator_database_url else None
    try:
        if settings.visual_ai_execution_enabled and material_database is None:
            raise RuntimeError("VISUAL_WORKER_DATABASE_REQUIRED")
        client = await connect_temporal(settings)
        material_activities = (
            WhatsAppMaterialActivities(
                processor := MaterialProcessor(
                    settings, material_database, MetaMediaClient(settings), MaterialStore(settings)
                ),
                AudioTranscriptionService(processor, OpenAIAudioTranscriber(settings)),
            )
            if material_database and settings.meta_encryption_key
            else None
        )
        editorial_activities = (
            EditorialActivities(
                EditorialProposalService(
                    settings, material_database, OpenAIEditorialProvider(settings), owner_database=database
                )
            )
            if material_database
            else None
        )
        media_activities = (
            MediaPreviewActivities(MediaPreviewService(settings, material_database, MaterialStore(settings), database))
            if material_database
            else None
        )
        content_activities = (
            ContentCandidateActivities(settings, database, material_database)
            if material_database and settings.meta_encryption_key
            else None
        )
        visual_activities = (
            VisualGenerationActivities(DatabaseVisualGenerationRunner(settings, database, material_database))
            if material_database and settings.visual_ai_execution_enabled
            else None
        )
        worker = Worker(
            client,
            task_queue=settings.temporal_task_queue,
            workflows=[BusinessCreatedWorkflow, BrandKitChangedWorkflow]
            + ([WhatsAppMaterialWorkflow] if material_activities else [])
            + ([EditorialProposalWorkflow] if editorial_activities else [])
            + ([StaticPreviewWorkflow] if media_activities else [])
            + ([VisualGenerationWorkflow] if visual_activities else [])
            + ([ContentCandidateWorkflow, FakeContentPublicationWorkflow] if content_activities else []),
            activities=[
                FoundationActivities(database).record_business_created,
                FoundationActivities(database).record_brand_kit_changed,
            ]
            + (
                [
                    material_activities.process_whatsapp_material,
                    material_activities.fail_whatsapp_material,
                    material_activities.transcribe_whatsapp_audio,
                ]
                if material_activities
                else []
            )
            + ([editorial_activities.generate_editorial_proposal] if editorial_activities else [])
            + ([media_activities.render_static_preview] if media_activities else [])
            + ([visual_activities.run_visual_generation] if visual_activities else [])
            + (
                [
                    content_activities.request_candidate_proposal,
                    content_activities.candidate_proposal_state,
                    content_activities.request_candidate_preview,
                    content_activities.candidate_preview_state,
                    content_activities.deliver_candidate_clarification,
                    content_activities.deliver_briefing_clarification,
                    content_activities.deliver_candidate_preview,
                    content_activities.publish_fake_content,
                ]
                if content_activities
                else []
            ),
            max_concurrent_activities=4,
        )
        await worker.run()
    finally:
        await database.close()
        if material_database:
            await material_database.close()


if __name__ == "__main__":
    asyncio.run(run_worker())
