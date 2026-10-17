from typing import Any

import numpy as np

from manim.animation.animation import DEFAULT_ANIMATION_RUN_TIME, Animation
from manim.constants import ORIGIN
from manim.mobject.mobject import Mobject
from manim.scene.scene import Scene
from manim.typing import Point3DLike, Vector3DLike
from manim.utils.rate_functions import RateFunction, linear


class MobjectAnimation(Animation):
    def __init__(
        self,
        mobject: Mobject,
        *,
        run_time: float = DEFAULT_ANIMATION_RUN_TIME,
        rate_func: RateFunction = linear,
    ) -> None:
        super().__init__(run_time=run_time, rate_func=rate_func)
        self.mobject = mobject

    def get_animated_mobjects(self) -> set[Mobject]:
        return {self.mobject}


class Add(MobjectAnimation):
    def __init__(
        self,
        mobject: Mobject,
        *,
        run_time: float = 0,
        rate_func: RateFunction = linear,
    ) -> None:
        super().__init__(mobject, run_time=run_time, rate_func=rate_func)

    def setup(self, scene: Scene) -> Any:
        scene.add(self.mobject)
        super().setup(scene)


class Remove(MobjectAnimation):
    def __init__(
        self,
        mobject: Mobject,
        *,
        run_time: float = 0,
        rate_func: RateFunction = linear,
    ) -> None:
        super().__init__(mobject, run_time=run_time, rate_func=rate_func)

    def setup(self, scene: Scene) -> Any:
        scene.remove(self.mobject)
        super().setup(scene)


class MoveTo(MobjectAnimation):
    def __init__(
        self,
        mobject: Mobject,
        point_or_mobject: Point3DLike | Mobject,
        *,
        aligned_edge: Vector3DLike = ORIGIN,
        run_time: float = DEFAULT_ANIMATION_RUN_TIME,
        rate_func: RateFunction = linear,
    ) -> None:
        super().__init__(mobject, run_time=run_time, rate_func=rate_func)
        self.point_or_mobject = point_or_mobject
        self.aligned_edge = aligned_edge

    def setup(self, scene: Scene) -> Any:
        self._start_point = self.mobject.get_critical_point(self.aligned_edge)
        self._target_point = (
            np.array(self.point_or_mobject)
            if not isinstance(self.point_or_mobject, Mobject)
            else self.point_or_mobject.get_critical_point(self.aligned_edge)
        )
        super().setup(scene)

    def update(self, alpha: float) -> Any:
        alpha = self.rate_func(alpha)
        point = (1 - alpha) * self._start_point + alpha * self._target_point
        self.mobject.move_to(point, aligned_edge=self.aligned_edge)


class AnimationGroup(Animation):
    def __init__(
        self,
        *animations: Animation,
        lag_ratio: float = 0.0,
        run_time: float = DEFAULT_ANIMATION_RUN_TIME,
        rate_func: RateFunction = linear,
    ) -> None:
        super().__init__(run_time=run_time, rate_func=rate_func)
        self.animations = animations
        self.lag_ratio = lag_ratio

    def setup(self, scene: Scene) -> Any:
        self._scene = scene
        self._started_animations: set[Animation] = set()
        self._finished_animations: set[Animation] = set()
        super().setup(scene)

    def update(self, alpha: float) -> Any:
        alpha = self.rate_func(alpha)
        self._timings = self._get_animation_timings()

        for (start, _), animation in zip(self._timings, self.animations, strict=True):
            if start <= alpha and animation not in self._started_animations:
                animation.setup(self._scene)
                self._started_animations.add(animation)

        for (start, end), animation in zip(self._timings, self.animations, strict=True):
            if (
                animation in self._started_animations
                and animation not in self._finished_animations
            ):
                animation_duration = end - start
                if animation_duration > 0:
                    animation_alpha = (alpha - start) / animation_duration
                    animation_alpha = max(0, min(animation_alpha, 1))
                else:
                    animation_alpha = 1
                animation.update(animation_alpha)

        for (_, end), animation in zip(self._timings, self.animations, strict=True):
            if end <= alpha and animation not in self._finished_animations:
                self._finished_animations.add(animation)

    def _get_animation_timings(self) -> list[tuple[float, float]]:
        start_and_end_times: list[tuple[float, float]] = []

        if self.run_time <= 0.0:
            return [(0, 0) for _ in self.animations]

        time = 0.0
        total_run_time = 0.0
        for animation in self.animations:
            start_time = time
            end_time = start_time + animation.run_time
            start_and_end_times.append((start_time, end_time))
            time += animation.run_time * self.lag_ratio
            total_run_time = max(total_run_time, end_time)

        if total_run_time <= 0.0:
            return start_and_end_times

        return [
            (start_time / total_run_time, end_time / total_run_time)
            for start_time, end_time in start_and_end_times
        ]

    def get_animated_mobjects(self) -> set[Mobject]:
        return {
            mobject
            for animation in self.animations
            for mobject in animation.get_animated_mobjects()
        }


class Succession(AnimationGroup):
    def __init__(
        self,
        *animations: Animation,
        lag_ratio: float = 1.0,
        run_time: float = DEFAULT_ANIMATION_RUN_TIME,
        rate_func: RateFunction = linear,
    ) -> None:
        super().__init__(
            *animations,
            lag_ratio=lag_ratio,
            run_time=run_time,
            rate_func=rate_func,
        )


class Wait(Animation):
    pass
