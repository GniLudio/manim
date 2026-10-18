"""Animate mobjects."""

from __future__ import annotations

from ..mobject import mobject
from ..mobject.mobject import Group, Mobject
from ..mobject.opengl import opengl_mobject
from ..utils.rate_functions import RateFunction, linear

__all__ = ["Animation", "Wait", "Add", "override_animation"]


from collections.abc import Callable
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from manim.scene.scene import Scene


DEFAULT_ANIMATION_RUN_TIME: float = 1.0
DEFAULT_ANIMATION_LAG_RATIO: float = 0.0


class Animation:
    def __init__(
        self,
        run_time: float = DEFAULT_ANIMATION_RUN_TIME,
        rate_func: RateFunction = linear,
    ) -> None:
        self.run_time = run_time
        self.rate_func = rate_func

    def setup(self, scene: Scene) -> None:
        self.update(0)

    def update(self, alpha: float) -> None:
        pass

    def finish(self, scene: Scene) -> None:
        self.update(1)

    def get_animated_mobjects(self) -> set[Mobject]:
        return set()


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


def prepare_animation(
    anim: Animation | mobject._AnimationBuilder | opengl_mobject._AnimationBuilder,
) -> Animation:
    r"""Returns either an unchanged animation, or the animation built
    from a passed animation factory.

    Examples
    --------

    ::

        >>> from manim import Square, FadeIn
        >>> s = Square()
        >>> prepare_animation(FadeIn(s))
        FadeIn(Square)

    ::

        >>> prepare_animation(s.animate.scale(2).rotate(42))
        _MethodAnimation(Square)

    ::

        >>> prepare_animation(42)
        Traceback (most recent call last):
        ...
        TypeError: Object 42 cannot be converted to an animation

    """
    if isinstance(anim, mobject._AnimationBuilder):
        return anim.build()

    if isinstance(anim, opengl_mobject._AnimationBuilder):
        return anim.build()

    if isinstance(anim, Animation):
        return anim

    raise TypeError(f"Object {anim} cannot be converted to an animation")


class Wait(Animation):
    pass


class Add(Animation):
    """Add Mobjects to a scene, without animating them in any other way. This
    is similar to the :meth:`.Scene.add` method, but :class:`Add` is an
    animation which can be grouped into other animations.

    Parameters
    ----------
    mobjects
        One :class:`~.Mobject` or more to add to a scene.
    run_time
        The duration of the animation after adding the ``mobjects``. Defaults
        to 0, which means this is an instant animation without extra wait time
        after adding them.
    **kwargs
        Additional arguments to pass to the parent :class:`Animation` class.

    Examples
    --------

    .. manim:: DefaultAddScene

        class DefaultAddScene(Scene):
            def construct(self):
                text_1 = Text("I was added with Add!")
                text_2 = Text("Me too!")
                text_3 = Text("And me!")
                texts = VGroup(text_1, text_2, text_3).arrange(DOWN)
                rect = SurroundingRectangle(texts, buff=0.5)

                self.play(
                    Create(rect, run_time=3.0),
                    Succession(
                        Wait(1.0),
                        # You can Add a Mobject in the middle of an animation...
                        Add(text_1),
                        Wait(1.0),
                        # ...or multiple Mobjects at once!
                        Add(text_2, text_3),
                    ),
                )
                self.wait()

    .. manim:: AddWithRunTimeScene

        class AddWithRunTimeScene(Scene):
            def construct(self):
                # A 5x5 grid of circles
                circles = VGroup(
                    *[Circle(radius=0.5) for _ in range(25)]
                ).arrange_in_grid(5, 5)

                self.play(
                    Succession(
                        # Add a run_time of 0.2 to wait for 0.2 seconds after
                        # adding the circle, instead of using Wait(0.2) after Add!
                        *[Add(circle, run_time=0.2) for circle in circles],
                        rate_func=smooth,
                    )
                )
                self.wait()
    """

    def __init__(
        self, *mobjects: Mobject, run_time: float = 0.0, **kwargs: Any
    ) -> None:
        mobject = mobjects[0] if len(mobjects) == 1 else Group(*mobjects)
        super().__init__(mobject, run_time=run_time, introducer=True, **kwargs)

    def begin(self) -> None:
        pass

    def finish(self) -> None:
        pass

    def clean_up_from_scene(self, scene: Scene) -> None:
        pass

    def update_mobjects(self, dt: float) -> None:
        pass

    def interpolate(self, alpha: float) -> None:
        pass


def override_animation(
    animation_class: type[Animation],
) -> Callable[[Callable], Callable]:
    """Decorator used to mark methods as overrides for specific :class:`~.Animation` types.

    Should only be used to decorate methods of classes derived from :class:`~.Mobject`.
    ``Animation`` overrides get inherited to subclasses of the ``Mobject`` who defined
    them. They don't override subclasses of the ``Animation`` they override.

    See Also
    --------
    :meth:`~.Mobject.add_animation_override`

    Parameters
    ----------
    animation_class
        The animation to be overridden.

    Returns
    -------
    Callable[[Callable], Callable]
        The actual decorator. This marks the method as overriding an animation.

    Examples
    --------

    .. manim:: OverrideAnimationExample

        class MySquare(Square):
            @override_animation(FadeIn)
            def _fade_in_override(self, **kwargs):
                return Create(self, **kwargs)

        class OverrideAnimationExample(Scene):
            def construct(self):
                self.play(FadeIn(MySquare()))

    """

    def decorator(func):
        func._override_animation = animation_class
        return func

    return decorator
