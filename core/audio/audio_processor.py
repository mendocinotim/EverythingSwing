import torch
import librosa
import nemo.collections.asr as nemo_asr
from pathlib import Path
import logging

class AudioProcessor:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.model = nemo_asr.models.EncDecCTCModel.from_pretrained(
            model_name="nvidia/speecht5_tts"
        )
        
    def process_audio(self, input_path: str):
        """Process audio using NeMo and librosa"""
        try:
            # Load audio with librosa (M1/M4 optimized)
            waveform, sample_rate = librosa.load(input_path, sr=16000, mono=True)
            
            # Convert to tensor
            waveform_tensor = torch.tensor(waveform).unsqueeze(0)
            
            # Transcribe with NeMo
            transcript = self.model.transcribe([waveform_tensor])[0]
            
            return {
                "status": "success",
                "transcript": transcript,
                "duration": len(waveform)/sample_rate
            }
            
        except Exception as e:
            self.logger.error(f"Processing failed: {str(e)}")
            return {"status": "error", "message": str(e)}
