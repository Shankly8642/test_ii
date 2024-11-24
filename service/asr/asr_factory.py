from .vosk_asr import VoskASR


class ASRFactory:
    @staticmethod
    def create_asr_pipeline(asr_type, **kwargs):
        if asr_type == "vosk":
            return VoskASR(**kwargs)
        else:
            raise ValueError(f"Не определен ASR: {asr_type}")
