import asyncio

from temporalio.client import Client
from temporalio.worker import Worker

from app.adapters.audio_transcription import OpenAIAudioTranscriber
from app.adapters.material_media import MaterialStore, MetaMediaClient
from app.core.config import Settings, get_settings
from app.core.logging import configure_logging
from app.db.session import Database
from app.services.audio_transcription import AudioTranscriptionService
from app.services.whatsapp_processing import MaterialProcessor
from app.workflows.activities import FoundationActivities
from app.workflows.foundation import BusinessCreatedWorkflow
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
    material_database = (
        Database(settings, correlator=True)
        if settings.correlator_database_url and settings.meta_encryption_key
        else None
    )
    try:
        client = await connect_temporal(settings)
        material_activities = (
            WhatsAppMaterialActivities(
                processor := MaterialProcessor(
                    settings, material_database, MetaMediaClient(settings), MaterialStore(settings)
                ),
                AudioTranscriptionService(processor, OpenAIAudioTranscriber(settings)),
            )
            if material_database
            else None
        )
        worker = Worker(
            client,
            task_queue=settings.temporal_task_queue,
            workflows=[BusinessCreatedWorkflow, WhatsAppMaterialWorkflow]
            if material_activities
            else [BusinessCreatedWorkflow],
            activities=[FoundationActivities(database).record_business_created]
            + (
                [
                    material_activities.process_whatsapp_material,
                    material_activities.fail_whatsapp_material,
                    material_activities.transcribe_whatsapp_audio,
                ]
                if material_activities
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
