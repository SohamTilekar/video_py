from typing import Callable, Sequence
from PIL import Image, ImageOps

from ..audio.AudioClip import SilenceClip, concatenate_audioclips, concatenate_audioclips
from .ImageSequenceClip import ImageSequenceClip
from .VideoClip import VideoClip


def composite_videoclips(clips: Sequence[VideoClip],
                         fps: int | float | None = None,
                         bg_color: tuple[int, ...] = (0, 0, 0, 0),
                         use_bg_clip: bool = False):
    frames: list[Image.Image] = []
    if use_bg_clip:
        bg_clip = clips[0]
        clips = clips[1:]
        fps = fps if fps is not None else max(
            clip.fps if clip.fps else 0.0 for clip in clips)
        if not fps:
            raise ValueError(
                'Provide fps for clips or at least one clip or fps parameter for composite_videoclips')
        td = 1/fps
        size = bg_clip.size
        duration: int | float = bg_clip.duration if bg_clip.duration else (_ for _ in  ()).throw(ValueError(f'Clip duration is not set, clip.__str__ = {bg_clip.__str__()}'))
        current_time = 0.0
        while current_time <= duration:
            frame = bg_clip.make_frame_pil(current_time)
            for clip in clips:
                if clip._st <= current_time <= clip._ed if clip._ed else clip.duration if clip.duration else float('inf'):
                    frame.paste(clip.make_frame_pil(current_time), clip.pos(current_time), clip.make_frame_pil(current_time) if clip.make_frame_pil(current_time).has_transparency_data else None)
            frames.append(frame)
            current_time += td
        return ImageSequenceClip(tuple(frames), fps=fps, duration=duration)
    else:
        fps = fps if fps is not None else max(
            clip.fps if clip.fps else 0.0 for clip in clips)
        if not fps:
            raise ValueError(
                'Provide fps for clips or at least one clip or fps parameter for composite_videoclips')
        td = 1/fps
        duration: int | float = 0.0
        max_size: tuple[int, int] = max(
            tuple(clip.size if clip.size and clip.size[0] and clip.size[1]
                  else (_ for _ in ()).throw(ValueError(f'Clip Size is not set, clip.__str__ = {clip.__str__()}')) for clip in clips))
        for clip in clips:
            clip_dur = clip.end - clip.start if clip.end else clip.duration - \
                clip.start if clip.duration else None
            if clip_dur and clip_dur > duration:
                duration: int | float = clip_dur
        if not duration:
            raise ValueError('Provide duration for clips or at least one clip')
        current_time = 0.0
        while current_time <= duration:
            current_frame = Image.new('RGBA', max_size, bg_color)
            for clip in clips:
                if clip.start <= current_time <= clip.end if clip.end else clip.duration if clip.duration else float('inf'):
                    tmp_clip_frame = clip.make_frame_pil(current_time)
                    current_frame.paste(
                        tmp_clip_frame,
                        clip.pos(current_time),
                        tmp_clip_frame if tmp_clip_frame.has_transparency_data else None)
            frames.append(current_frame)
            current_time += td
        return ImageSequenceClip(tuple(frames), fps=fps, duration=duration)


def concatenate_videoclips(clips: tuple[VideoClip] | list[VideoClip],
                           transparent: bool = False,
                           fps: int | float | None = None,
                           scaling_strategy: bool | None = None,
                           transition: VideoClip | Callable[[
                               Image.Image, Image.Image, int | float], VideoClip] | None = None,
                           audio: bool = True,
                           audio_fps: int | None = None,
                           ):
    # TODO: Add transition support
    fps = fps if fps is not None else max(
        clip.fps if clip.fps else 0.0 for clip in clips)
    duration_per_clip: list[int | float] = [clip.end if clip.end else
                                            clip.duration if clip.duration else
                                            (_ for _ in ()).throw(ValueError(
                                                f'Clip duration and end is not set __str__={clip.__str__()}'))
                                            for clip in clips]
    td = 1/fps
    duration: int | float = sum(duration_per_clip)

    if scaling_strategy is None:
        def increase_scale(frame: Image.Image, new_size: tuple[int, int]) -> Image.Image:
            new_frame = Image.new('RGBA' if transparent else 'RGB', new_size)
            new_frame.paste(
                frame, (new_size[0]//2 - frame.size[0]//2, new_size[1]//2 - frame.size[1]//2))
            return new_frame

        size: tuple[int, int] = max(tuple(clip.size if
                                          clip.size and clip.size[0] and clip.size[1]
                                          else (_ for _ in ()).throw(ValueError(f'Clip Size is not set, clip.__str__ = {clip.__str__()}')) for clip in clips))

        frames = []
        for i, clip in enumerate(clips):
            current_clip_current_time = 0.0
            while current_clip_current_time <= duration_per_clip[i]:
                current_clip_current_frame = clip.make_frame_pil(
                    current_clip_current_time)
                current_clip_current_frame = increase_scale(
                    current_clip_current_frame, size)
                frames.append(current_clip_current_frame)
                current_clip_current_time += td
        f_frames = tuple(frames)
        del frames

        if audio:
            audios = []
            for i, clip in enumerate(clips):
                if clip.audio is not None:
                    audios.append(clip.audio)
                else:
                    audios.append(SilenceClip(duration=duration_per_clip[i]))
            return ImageSequenceClip(f_frames, fps=fps, duration=duration, audio=concatenate_audioclips(audios, fps=audio_fps))
        else:
            return ImageSequenceClip(f_frames, fps=fps, duration=duration)

    elif scaling_strategy is True:
        def increase_scale(frame: Image.Image, new_size: tuple[int, int]) -> Image.Image:
            return ImageOps.pad(frame, new_size, color=(0, 0, 0, 0)).convert('RGBA' if transparent else 'RGB')

        size: tuple[int, int] = max(tuple(clip.size if
                                          clip.size and clip.size[0] and clip.size[1]
                                          else (_ for _ in ()).throw(ValueError(f'Clip Size is not set, clip.__str__ = {clip.__str__()}')) for clip in clips))
        frames = []
        for i, clip in enumerate(clips):
            current_clip_current_time = 0.0
            while current_clip_current_time <= duration_per_clip[i]:
                current_clip_current_frame = clip.make_frame_pil(
                    current_clip_current_time)
                current_clip_current_frame = increase_scale(
                    current_clip_current_frame, size)
                frames.append(current_clip_current_frame)
                current_clip_current_time += td
        f_frames = tuple(frames)
        del frames

        if audio:
            audios = []
            for i, clip in enumerate(clips):
                if clip.audio is not None:
                    audios.append(clip.audio)
                else:
                    audios.append(SilenceClip(duration=duration_per_clip[i]))
            return ImageSequenceClip(f_frames, fps=fps, duration=duration, audio=concatenate_audioclips(audios, fps=audio_fps))
        else:
            return ImageSequenceClip(f_frames, fps=fps, duration=duration)
    elif scaling_strategy is False:
        def increase_scale(frame: Image.Image, new_size: tuple[int, int]) -> Image.Image:
            return ImageOps.fit(frame, new_size).convert('RGBA' if transparent else 'RGB')

        size: tuple[int, int] = max(tuple(clip.size if
                                          clip.size and clip.size[0] and clip.size[1]
                                          else (_ for _ in ()).throw(ValueError(f'Clip Size is not set, clip.__str__ = {clip.__str__()}')) for clip in clips))
        frames = []
        for i, clip in enumerate(clips):
            current_clip_current_time = 0.0
            while current_clip_current_time <= duration_per_clip[i]:
                current_clip_current_frame = clip.make_frame_pil(
                    current_clip_current_time)
                current_clip_current_frame = increase_scale(
                    current_clip_current_frame, size)
                frames.append(current_clip_current_frame)
                current_clip_current_time += td
        f_frames = tuple(frames)
        del frames

        if audio:
            audios = []
            for i, clip in enumerate(clips):
                if clip.audio is not None:
                    audios.append(clip.audio)
                else:
                    audios.append(SilenceClip(duration=duration_per_clip[i]))
            return ImageSequenceClip(f_frames, fps=fps, duration=duration, audio=concatenate_audioclips(audios, fps=audio_fps))
        else:
            return ImageSequenceClip(f_frames, fps=fps, duration=duration)
    else:
        raise TypeError(f'scaling_strategy must be bool or None, not {
                        type(scaling_strategy)}')
