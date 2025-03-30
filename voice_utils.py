import os
import io
import wave
import pyaudio
import numpy as np
import sounddevice as sd
import soundfile as sf
from openai import OpenAI
import time

class VoiceInterface:
    def __init__(self, 
                 sample_rate=16000, 
                 channels=1, 
                 chunk=1024, 
                 record_seconds=5, 
                 silence_threshold=0.01):
        """
        Initialize voice interface parameters
        
        Args:
            sample_rate (int): Audio sampling rate
            channels (int): Number of audio channels
            chunk (int): Number of audio frames per buffer
            record_seconds (int): Maximum recording duration
            silence_threshold (float): Noise level to detect silence
        """
        self.sample_rate = sample_rate
        self.channels = channels
        self.chunk = chunk
        self.record_seconds = record_seconds
        self.silence_threshold = silence_threshold
        
        # Initialize OpenAI client for STT and TTS
        self.openai_client = OpenAI()
        
        # Temporary directory for audio files
        self.temp_dir = 'temp_audio'
        os.makedirs(self.temp_dir, exist_ok=True)

    def record_audio(self):
        """
        Record audio from microphone with silence detection
        
        Returns:
            str: Path to recorded audio file
        """
        print("Listening... (speak now)")
        
        # Initialize PyAudio
        p = pyaudio.PyAudio()
        stream = p.open(format=pyaudio.paFloat32,
                        channels=self.channels,
                        rate=self.sample_rate,
                        input=True,
                        frames_per_buffer=self.chunk)

        frames = []
        silence_counter = 0
        max_silence_duration = int(self.sample_rate / self.chunk * 60)  # 1 second of silence

        for _ in range(0, int(self.sample_rate / self.chunk * self.record_seconds)):
            data = stream.read(self.chunk)
            audio_data = np.frombuffer(data, dtype=np.float32)
            frames.append(audio_data)

            # Silence detection
            rms = np.sqrt(np.mean(audio_data**2))
            if rms < self.silence_threshold:
                silence_counter += 1
            else:
                silence_counter = 0

            # Stop recording if prolonged silence detected
            if silence_counter > max_silence_duration:
                break

        # Stop and close the stream
        stream.stop_stream()
        stream.close()
        p.terminate()

        # Save the recorded audio
        output_path = os.path.join(self.temp_dir, f'recording_{int(time.time())}.wav')
        
        # Write to WAV file
        with wave.open(output_path, 'wb') as wf:
            wf.setnchannels(self.channels)
            wf.setsampwidth(pyaudio.PyAudio().get_sample_size(pyaudio.paFloat32))
            wf.setframerate(self.sample_rate)
            wf.writeframes(np.array(frames).tobytes())

        print("Recording complete.")
        return output_path

    def transcribe_audio(self, audio_path):
        """
        Transcribe audio using OpenAI Whisper
        
        Args:
            audio_path (str): Path to audio file
        
        Returns:
            str: Transcribed text
        """
        try:
            with open(audio_path, "rb") as audio_file:
                transcription = self.openai_client.audio.transcriptions.create(
                    model="whisper-1", 
                    file=audio_file
                )
            return transcription.text
        except Exception as e:
            print(f"Transcription error: {e}")
            return ""

    def text_to_speech(self, text, output_path=None):
        """
        Convert text to speech using OpenAI TTS
        
        Args:
            text (str): Text to convert to speech
            output_path (str, optional): Path to save audio file
        
        Returns:
            str: Path to generated audio file
        """
        try:
            # Generate speech
            response = self.openai_client.audio.speech.create(
                model="tts-1",
                voice="alloy",  # Can be: alloy, echo, fable, onyx, nova, shimmer
                input=text
            )

            # Generate output path if not provided
            if output_path is None:
                output_path = os.path.join(self.temp_dir, f'speech_{int(time.time())}.mp3')

            # Save the speech file
            with open(output_path, 'wb') as audio_file:
                audio_file.write(response.content)

            # Play the audio
            self._play_audio(output_path)

            return output_path
        except Exception as e:
            print(f"Text-to-speech error: {e}")
            return ""

    def _play_audio(self, audio_path):
        """
        Play audio file using sounddevice
        
        Args:
            audio_path (str): Path to audio file
        """
        try:
            # Read the audio file
            data, fs = sf.read(audio_path)
            sd.play(data, fs)
            sd.wait()
        except Exception as e:
            print(f"Audio playback error: {e}")