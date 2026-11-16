"""Internal transcription tariff; consumed inside the piece's single budget.

Source checked 2026-11-16:
https://developers.openai.com/api/docs/models/gpt-transcribe.md
Published duration price: USD 0.0045/minute. Reserving whole minutes rounds
up conservatively; the reservation and estimate are not a provider invoice.
"""

TRANSCRIPTION_MODEL = "gpt-transcribe"
TARIFF_VERSION = "gpt-transcribe-duration-2026-11-16"
USD_MICROS_PER_MINUTE = 4_500


def transcription_cost(seconds: int) -> tuple[int, int]:
    if type(seconds) is not int or not 1 <= seconds <= 180:
        raise ValueError("AUDIO_DURATION_INVALID")
    reservation = ((seconds + 59) // 60) * USD_MICROS_PER_MINUTE
    estimate = (seconds * USD_MICROS_PER_MINUTE + 59) // 60
    return reservation, estimate
