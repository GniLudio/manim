"""Tools for displaying multiple animations at once."""

from __future__ import annotations

from collections.abc import Callable, Iterable
from typing import TYPE_CHECKING, Any

from manim.animation.animation import (
    DEFAULT_ANIMATION_RUN_TIME,
    Animation,
    MobjectAnimation,
)
from manim.mobject.mobject import Mobject
from manim.scene.scene import Scene
from manim.utils.rate_functions import RateFunction, linear

if TYPE_CHECKING:
    pass

__all__ = [
    "AnimationGroup",
    "Succession",
    "LaggedStart",
    "LaggedStartMap",
    "Add",
    "Remove",
]


DEFAULT_LAGGED_START_LAG_RATIO: float = 0.05


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

    def setup(self) -> None:
        self._started_animations: set[Animation] = set()
        self._finished_animations: set[Animation] = set()
        super().setup()

    def update(self, alpha: float) -> None:
        alpha = self.rate_func(alpha)
        self._timings = self._get_animation_timings()

        for (start, end), animation in zip(self._timings, self.animations, strict=True):
            if start <= alpha and animation not in self._started_animations:
                animation.setup()
                self._started_animations.add(animation)

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

            if end <= alpha and animation not in self._finished_animations:
                animation.finish()
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


class LaggedStart(AnimationGroup):
    """Adjusts the timing of a series of :class:`~.Animation` according to ``lag_ratio``.

    Parameters
    ----------
    animations
        Sequence of :class:`~.Animation` objects to be played.
    lag_ratio
        Defines the delay after which the animation is applied to submobjects. A lag_ratio of
        ``n.nn`` means the next animation will play when ``nnn%`` of the current animation has played.
        Defaults to 0.05, meaning that the next animation will begin when 5% of the current
        animation has played.

        This does not influence the total runtime of the animation. Instead the runtime
        of individual animations is adjusted so that the complete animation has the defined
        run time.

    Examples
    --------
    .. manim:: LaggedStartExample

        class LaggedStartExample(Scene):
            def construct(self):
                title = Text("lag_ratio = 0.25").to_edge(UP)

                dot1 = Dot(point=LEFT * 2 + UP, radius=0.16)
                dot2 = Dot(point=LEFT * 2, radius=0.16)
                dot3 = Dot(point=LEFT * 2 + DOWN, radius=0.16)
                line_25 = DashedLine(
                    start=LEFT + UP * 2,
                    end=LEFT + DOWN * 2,
                    color=RED
                )
                label = Text("25%", font_size=24).next_to(line_25, UP)
                self.add(title, dot1, dot2, dot3, line_25, label)

                self.play(LaggedStart(
                    dot1.animate.shift(RIGHT * 4),
                    dot2.animate.shift(RIGHT * 4),
                    dot3.animate.shift(RIGHT * 4),
                    lag_ratio=0.25,
                    run_time=4
                ))
    """

    def __init__(
        self,
        *animations: Animation,
        lag_ratio: float = DEFAULT_LAGGED_START_LAG_RATIO,
        **kwargs: Any,
    ):
        super().__init__(*animations, lag_ratio=lag_ratio, **kwargs)


class LaggedStartMap(LaggedStart):
    """Plays a series of :class:`~.Animation` while mapping a function to submobjects.

    Parameters
    ----------
    animation_class
        :class:`~.Animation` to apply to mobject.
    mobject
        :class:`~.Mobject` whose submobjects the animation, and optionally the function,
        are to be applied.
    arg_creator
        Function which will be applied to :class:`~.Mobject`.
    run_time
        The duration of the animation in seconds.
    lag_ratio
        Defines the delay after which the animation is applied to submobjects. A lag_ratio of
        ``n.nn`` means the next animation will play when ``nnn%`` of the current animation has played.
        Defaults to 0.05, meaning that the next animation will begin when 5% of the current
        animation has played.

        This does not influence the total runtime of the animation. Instead the runtime
        of individual animations is adjusted so that the complete animation has the defined
        run time.
    kwargs
        Further keyword arguments that are passed to `animation_class`.

    Examples
    --------
    .. manim:: LaggedStartMapExample

        class LaggedStartMapExample(Scene):
            def construct(self):
                title = Tex("LaggedStartMap").to_edge(UP, buff=LARGE_BUFF)
                dots = VGroup(
                    *[Dot(radius=0.16) for _ in range(35)]
                    ).arrange_in_grid(rows=5, cols=7, buff=MED_LARGE_BUFF)
                self.add(dots, title)

                # Animate yellow ripple effect
                for mob in dots, title:
                    self.play(LaggedStartMap(
                        ApplyMethod, mob,
                        lambda m : (m.set_color, YELLOW),
                        lag_ratio = 0.1,
                        rate_func = there_and_back,
                        run_time = 2
                    ))
    """

    def __init__(
        self,
        animation_class: type[Animation],
        mobject: Mobject,
        arg_creator: Callable[[Mobject], Iterable[Any]] | None = None,
        run_time: float = 2,
        lag_ratio: float = DEFAULT_LAGGED_START_LAG_RATIO,
        **kwargs: Any,
    ):
        if arg_creator is None:

            def identity(mob: Mobject) -> tuple[Mobject]:
                return (mob,)

            arg_creator = identity

        args_list = [arg_creator(submob) for submob in mobject]
        anim_kwargs = dict(kwargs)
        if "lag_ratio" in anim_kwargs:
            anim_kwargs.pop("lag_ratio")
        animations = [animation_class(*args, **anim_kwargs) for args in args_list]
        super().__init__(*animations, run_time=run_time, lag_ratio=lag_ratio)


class Add(MobjectAnimation):
    def __init__(
        self,
        mobject: Mobject,
        scene: Scene,
        *,
        run_time: float = 0,
        rate_func: RateFunction = linear,
    ) -> None:
        super().__init__(mobject, run_time=run_time, rate_func=rate_func)
        self.scene = scene

    def setup(self) -> None:
        self.scene.add(self.mobject)
        super().setup()


class Remove(MobjectAnimation):
    def __init__(
        self,
        mobject: Mobject,
        scene: Scene,
        *,
        run_time: float = 0,
        rate_func: RateFunction = linear,
    ) -> None:
        super().__init__(mobject, run_time=run_time, rate_func=rate_func)
        self.scene = scene

    def setup(self) -> None:
        self.scene.remove(self.mobject)
        super().setup()
