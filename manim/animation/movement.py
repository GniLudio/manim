"""Animations related to movement."""

from __future__ import annotations

from manim.constants import ORIGIN
from manim.mobject.mobject import Mobject
from manim.typing import Point3DLike, Vector3DLike

__all__ = [
    "Homotopy",
    "SmoothedVectorizedHomotopy",
    "ComplexHomotopy",
    "PhaseFlow",
    "MoveAlongPath",
    "MoveTo",
]

from collections.abc import Callable
from typing import TYPE_CHECKING, Any

import numpy as np

from ..animation.animation import (
    DEFAULT_ANIMATION_RUN_TIME,
    Animation,
    MobjectAnimation,
)
from ..utils.rate_functions import linear

if TYPE_CHECKING:
    from typing import Self

    from manim.mobject.types.vectorized_mobject import VMobject
    from manim.typing import MappingFunction, Point3D
    from manim.utils.rate_functions import RateFunction


class Homotopy(Animation):
    """A Homotopy.

    This is an animation transforming the points of a mobject according
    to the specified transformation function. With the parameter :math:`t`
    moving from 0 to 1 throughout the animation and :math:`(x, y, z)`
    describing the coordinates of the point of a mobject,
    the function passed to the ``homotopy`` keyword argument should
    transform the tuple :math:`(x, y, z, t)` to :math:`(x', y', z')`,
    the coordinates the original point is transformed to at time :math:`t`.

    Parameters
    ----------
    homotopy
        A function mapping :math:`(x, y, z, t)` to :math:`(x', y', z')`.
    mobject
        The mobject transformed under the given homotopy.
    run_time
        The run time of the animation.
    apply_function_kwargs
        Keyword arguments propagated to :meth:`.Mobject.apply_function`.
    kwargs
        Further keyword arguments passed to the parent class.

    Examples
    --------

    .. manim:: HomotopyExample

        class HomotopyExample(Scene):
            def construct(self):
                square = Square()

                def homotopy(x, y, z, t):
                    if t <= 0.25:
                        progress = t / 0.25
                        return (x, y + progress * 0.2 * np.sin(x), z)
                    else:
                        wave_progress = (t - 0.25) / 0.75
                        return (x, y + 0.2 * np.sin(x + 10 * wave_progress), z)

                self.play(Homotopy(homotopy, square, rate_func= linear, run_time=2))

    """

    def __init__(
        self,
        homotopy: Callable[[float, float, float, float], tuple[float, float, float]],
        mobject: Mobject,
        run_time: float = 3,
        apply_function_kwargs: dict[str, Any] | None = None,
        **kwargs: Any,
    ):
        self.homotopy = homotopy
        self.apply_function_kwargs = (
            apply_function_kwargs if apply_function_kwargs is not None else {}
        )
        super().__init__(mobject, run_time=run_time, **kwargs)

    def function_at_time_t(self, t: float) -> MappingFunction:
        def mapping_function(p: Point3D) -> Point3D:
            x, y, z = p
            return np.array(self.homotopy(x, y, z, t))

        return mapping_function

    def interpolate_submobject(
        self,
        submobject: Mobject,
        starting_submobject: Mobject,
        alpha: float,
    ) -> Self:
        submobject.points = starting_submobject.points
        submobject.apply_function(
            self.function_at_time_t(alpha),
            **self.apply_function_kwargs,
        )
        return self


class SmoothedVectorizedHomotopy(Homotopy):
    def interpolate_submobject(
        self,
        submobject: Mobject,
        starting_submobject: Mobject,
        alpha: float,
    ) -> Self:
        assert isinstance(submobject, VMobject)
        super().interpolate_submobject(submobject, starting_submobject, alpha)
        submobject.make_smooth()
        return self


class ComplexHomotopy(Homotopy):
    def __init__(
        self,
        complex_homotopy: Callable[[complex, float], float],
        mobject: Mobject,
        **kwargs: Any,
    ):
        """Complex Homotopy a function Cx[0, 1] to C"""

        def homotopy(
            x: float,
            y: float,
            z: float,
            t: float,
        ) -> tuple[float, float, float]:
            c = complex_homotopy(complex(x, y), t)
            return (c.real, c.imag, z)

        super().__init__(homotopy, mobject, **kwargs)


class PhaseFlow(Animation):
    def __init__(
        self,
        function: Callable[[np.ndarray], np.ndarray],
        mobject: Mobject,
        virtual_time: float = 1,
        suspend_mobject_updating: bool = False,
        rate_func: RateFunction = linear,
        **kwargs: Any,
    ):
        self.virtual_time = virtual_time
        self.function = function
        super().__init__(
            mobject,
            suspend_mobject_updating=suspend_mobject_updating,
            rate_func=rate_func,
            **kwargs,
        )

    def interpolate_mobject(self, alpha: float) -> None:
        if hasattr(self, "last_alpha"):
            dt = self.virtual_time * (
                self.rate_func(alpha) - self.rate_func(self.last_alpha)
            )
            self.mobject.apply_function(lambda p: p + dt * self.function(p))
        self.last_alpha: float = alpha


class MoveAlongPath(Animation):
    """Make one mobject move along the path of another mobject.

    .. manim:: MoveAlongPathExample

        class MoveAlongPathExample(Scene):
            def construct(self):
                d1 = Dot().set_color(ORANGE)
                l1 = Line(LEFT, RIGHT)
                l2 = VMobject()
                self.add(d1, l1, l2)
                l2.add_updater(lambda x: x.become(Line(LEFT, d1.get_center()).set_color(ORANGE)))
                self.play(MoveAlongPath(d1, l1), rate_func=linear)
    """

    def __init__(
        self,
        mobject: Mobject,
        path: VMobject,
        suspend_mobject_updating: bool = False,
        **kwargs: Any,
    ):
        self.path = path
        super().__init__(
            mobject, suspend_mobject_updating=suspend_mobject_updating, **kwargs
        )

    def interpolate_mobject(self, alpha: float) -> None:
        point = self.path.point_from_proportion(self.rate_func(alpha))
        self.mobject.move_to(point)


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

    def setup(self) -> None:
        self._start_point = self.mobject.get_critical_point(self.aligned_edge)
        self._target_point = (
            np.array(self.point_or_mobject)
            if not isinstance(self.point_or_mobject, Mobject)
            else self.point_or_mobject.get_critical_point(self.aligned_edge)
        )
        super().setup()

    def update(self, alpha: float) -> None:
        alpha = self.rate_func(alpha)
        point = (1 - alpha) * self._start_point + alpha * self._target_point
        self.mobject.move_to(point, aligned_edge=self.aligned_edge)
