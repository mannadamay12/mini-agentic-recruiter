import os
import io
import wave
import pyaudio
import numpy as np
import sounddevice as sd
import soundfile as sf
from openai import OpenAI
import time
import threading

class VoiceInterface:
    def __init__(self, 
                 sample_rate=48000, 
                 channels=1, 
                 chunk=1024, 
                 record_seconds=60, 
                 silence_threshold=500):
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
        
        # Audio playback status
        self.is_playing = False

    def record_audio(self, silence_limit_sec=2.0):
        """
        Record audio from microphone with silence detection

        Args:
            silence_limit_sec (float): Seconds of silence after speech to stop recording.
        
        Returns:
            str: Path to recorded audio file
        """
        print("\n[System] Listening... (speak now)")
        
        # Initialize PyAudio
        p = pyaudio.PyAudio()
        
        # Find the appropriate input device
        input_device_index = None
        info = p.get_host_api_info_by_index(0)
        num_devices = info.get('deviceCount')
        
        # Debugging device info
        print("\n[System] Available audio input devices:")
        for i in range(num_devices):
            device_info = p.get_device_info_by_index(i)
            if device_info.get('maxInputChannels') > 0:
                print(f"[System] ID: {i}, Name: {device_info.get('name')}")
                # Default to the first input device we find
                if input_device_index is None:
                    input_device_index = i
        
        # Try to open the stream with the selected device
        try:
            stream = p.open(format=pyaudio.paInt16,
                          channels=self.channels,
                          rate=self.sample_rate,
                          input=True,
                          frames_per_buffer=self.chunk,
                          input_device_index=input_device_index)
        except Exception as e:
            print(f"[System] Error opening audio device {input_device_index}: {e}")
            print("[System] Trying default device...")
            stream = p.open(format=pyaudio.paInt16,
                          channels=self.channels,
                          rate=self.sample_rate,
                          input=True,
                          frames_per_buffer=self.chunk)

        frames = []
        silence_counter = 0
        speaking_started = False
        max_silence_frames = int((self.sample_rate / self.chunk) * silence_limit_sec)
        max_record_frames = int((self.sample_rate / self.chunk) * self.record_seconds)
        recorded_frames = 0

        while recorded_frames < max_record_frames:
            try:
                data = stream.read(self.chunk, exception_on_overflow=False)
                frames.append(data)
                recorded_frames += 1
                
                # Convert to numpy array for RMS calculation
                audio_data = np.frombuffer(data, dtype=np.int16)
                mean_squared = np.nanmean(audio_data**2)
                if np.isnan(mean_squared) or mean_squared < 0:
                    rms = 0
                else:
                    rms = np.sqrt(mean_squared)
                
                if rms > self.silence_threshold:
                    if not speaking_started:
                        print("[System] Speech detected...")
                    speaking_started = True
                    silence_counter = 0
                elif speaking_started:
                    # Only count silence after speaking has started
                    silence_counter += 1

                # Stop recording if sustained silence detected AFTER speech
                if speaking_started and silence_counter > max_silence_frames:
                    print(f"[System] Silence detected. Stopping recording.")
                    break
            except IOError as e:
                print(f"[System] Warning: Input error ({e}). Continuing...")
                time.sleep(0.01)

        # If loop finished without speech starting
        if not speaking_started:
            print("[System] No speech detected within the time limit.")
            stream.stop_stream()
            stream.close()
            p.terminate()
            return self.record_audio(silence_limit_sec)  # Try again

        print("[System] Recording complete.")
        stream.stop_stream()
        stream.close()
        p.terminate()

        output_path = os.path.join(self.temp_dir, f'recording_{int(time.time())}.wav')
        
        try:
            wf = wave.open(output_path, 'wb')
            wf.setnchannels(self.channels)
            wf.setsampwidth(p.get_sample_size(pyaudio.paInt16))
            wf.setframerate(self.sample_rate)
            wf.writeframes(b''.join(frames))
            wf.close()
        except Exception as write_error:
            print(f"[System] Error writing audio file: {write_error}")
            return None

        return output_path

    def transcribe_audio(self, audio_path):
        """
        Transcribe audio using OpenAI Whisper
        
        Args:
            audio_path (str): Path to audio file
        
        Returns:
            str: Transcribed text
        """
        if not audio_path or not os.path.exists(audio_path):
            print("[System] No valid audio file to transcribe")
            return ""
            
        try:
            print("[System] Transcribing audio...")
            with open(audio_path, "rb") as audio_file:
                transcription = self.openai_client.audio.transcriptions.create(
                    model="whisper-1", 
                    file=audio_file
                )
            return transcription.text
        except Exception as e:
            print(f"[System] Transcription error: {e}")
            return ""

    def text_to_speech(self, text, output_path=None, voice="alloy"):
        """
        Convert text to speech using OpenAI TTS
        
        Args:
            text (str): Text to convert to speech
            output_path (str, optional): Path to save audio file
            voice (str): Voice to use (alloy, echo, fable, onyx, nova, shimmer)
        
        Returns:
            str: Path to generated audio file
        """
        if not text:
            return ""
            
        try:
            # Generate speech
            response = self.openai_client.audio.speech.create(
                model="tts-1-hd",  # Using high-definition model
                voice=voice,
                input=text
            )

            # Generate output path if not provided
            if output_path is None:
                output_path = os.path.join(self.temp_dir, f'speech_{int(time.time())}.mp3')

            # Save the speech file
            with open(output_path, 'wb') as audio_file:
                audio_file.write(response.content)

            # Play the audio in a separate thread
            self._play_audio_async(output_path)

            return output_path
        except Exception as e:
            print(f"[System] Text-to-speech error: {e}")
            return ""

    def _play_audio(self, audio_path):
        """
        Play audio file using sounddevice
        
        Args:
            audio_path (str): Path to audio file
        """
        try:
            self.is_playing = True
            data, fs = sf.read(audio_path)
            sd.play(data, fs)
            sd.wait()
            self.is_playing = False
        except Exception as e:
            print(f"[System] Audio playback error: {e}")
            self.is_playing = False
            
    def _play_audio_async(self, audio_path):
        """
        Play audio file asynchronously
        
        Args:
            audio_path (str): Path to audio file
        """
        # Wait for any current playback to finish
        while self.is_playing:
            time.sleep(0.1)
            
        # Start playback in a new thread
        audio_thread = threading.Thread(target=self._play_audio, args=(audio_path,))
        audio_thread.daemon = True
        audio_thread.start()

    def adjust_for_meeting(self):
        """
        Adjust audio settings for optimal performance in a meeting context
        """
        # Lower the silence threshold for better speech detection in meeting environments
        self.silence_threshold = 300
        
        # Increase record seconds for longer responses in meeting context
        self.record_seconds = 120
        
        # Adjust chunk size for better meeting audio processing
        self.chunk = 2048
        
        print("[System] Voice interface adjusted for meeting environment")