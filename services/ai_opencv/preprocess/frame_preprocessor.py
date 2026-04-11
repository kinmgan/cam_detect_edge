from ingestion.preprocessor import Preprocessor


class FrameQualityPreprocessor:
    def __init__(self, motion_threshold: float = 0.5):
        self.preprocessor = Preprocessor(motion_threshold=motion_threshold)

    def process(self, frame_packet):
        return self.preprocessor.analyze(frame_packet)
