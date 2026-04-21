import ctypes
from _typeshed import Incomplete

lib: str
lib_name: Incomplete

c_int32 = ctypes.c_int32
c_uint32 = ctypes.c_uint32
c_uint8: Incomplete
c_size_t = ctypes.c_size_t
c_bool = ctypes.c_bool
c_double = ctypes.c_double
c_char_p = ctypes.c_char_p
c_void_p = ctypes.c_void_p

MLX_KEY_SPACE: int
MLX_KEY_APOSTROPHE: int
MLX_KEY_COMMA: int
MLX_KEY_MINUS: int
MLX_KEY_PERIOD: int
MLX_KEY_SLASH: int
MLX_KEY_0: int
MLX_KEY_1: int
MLX_KEY_2: int
MLX_KEY_3: int
MLX_KEY_4: int
MLX_KEY_5: int
MLX_KEY_6: int
MLX_KEY_7: int
MLX_KEY_8: int
MLX_KEY_9: int
MLX_KEY_SEMICOLON: int
MLX_KEY_EQUAL: int
MLX_KEY_A: int
MLX_KEY_B: int
MLX_KEY_C: int
MLX_KEY_D: int
MLX_KEY_E: int
MLX_KEY_F: int
MLX_KEY_G: int
MLX_KEY_H: int
MLX_KEY_I: int
MLX_KEY_J: int
MLX_KEY_K: int
MLX_KEY_L: int
MLX_KEY_M: int
MLX_KEY_N: int
MLX_KEY_O: int
MLX_KEY_P: int
MLX_KEY_Q: int
MLX_KEY_R: int
MLX_KEY_S: int
MLX_KEY_T: int
MLX_KEY_U: int
MLX_KEY_V: int
MLX_KEY_W: int
MLX_KEY_X: int
MLX_KEY_Y: int
MLX_KEY_Z: int
MLX_KEY_LEFT_BRACKET: int
MLX_KEY_BACKSLASH: int
MLX_KEY_RIGHT_BRACKET: int
MLX_KEY_GRAVE_ACCENT: int
MLX_KEY_ESCAPE: int
MLX_KEY_ENTER: int
MLX_KEY_TAB: int
MLX_KEY_BACKSPACE: int
MLX_KEY_INSERT: int
MLX_KEY_DELETE: int
MLX_KEY_RIGHT: int
MLX_KEY_LEFT: int
MLX_KEY_DOWN: int
MLX_KEY_UP: int
MLX_KEY_PAGE_UP: int
MLX_KEY_PAGE_DOWN: int
MLX_KEY_HOME: int
MLX_KEY_END: int
MLX_KEY_CAPS_LOCK: int
MLX_KEY_SCROLL_LOCK: int
MLX_KEY_NUM_LOCK: int
MLX_KEY_PRINT_SCREEN: int
MLX_KEY_PAUSE: int
MLX_KEY_F1: int
MLX_KEY_F2: int
MLX_KEY_F3: int
MLX_KEY_F4: int
MLX_KEY_F5: int
MLX_KEY_F6: int
MLX_KEY_F7: int
MLX_KEY_F8: int
MLX_KEY_F9: int
MLX_KEY_F10: int
MLX_KEY_F11: int
MLX_KEY_F12: int
MLX_KEY_F13: int
MLX_KEY_F14: int
MLX_KEY_F15: int
MLX_KEY_F16: int
MLX_KEY_F17: int
MLX_KEY_F18: int
MLX_KEY_F19: int
MLX_KEY_F20: int
MLX_KEY_F21: int
MLX_KEY_F22: int
MLX_KEY_F23: int
MLX_KEY_F24: int
MLX_KEY_F25: int
MLX_KEY_KP_0: int
MLX_KEY_KP_1: int
MLX_KEY_KP_2: int
MLX_KEY_KP_3: int
MLX_KEY_KP_4: int
MLX_KEY_KP_5: int
MLX_KEY_KP_6: int
MLX_KEY_KP_7: int
MLX_KEY_KP_8: int
MLX_KEY_KP_9: int
MLX_KEY_KP_DECIMAL: int
MLX_KEY_KP_DIVIDE: int
MLX_KEY_KP_MULTIPLY: int
MLX_KEY_KP_SUBTRACT: int
MLX_KEY_KP_ADD: int
MLX_KEY_KP_ENTER: int
MLX_KEY_KP_EQUAL: int
MLX_KEY_LEFT_SHIFT: int
MLX_KEY_LEFT_CONTROL: int
MLX_KEY_LEFT_ALT: int
MLX_KEY_LEFT_SUPER: int
MLX_KEY_RIGHT_SHIFT: int
MLX_KEY_RIGHT_CONTROL: int
MLX_KEY_RIGHT_ALT: int
MLX_KEY_RIGHT_SUPER: int
MLX_KEY_MENU: int
MLX_CURSOR_ARROW: int
MLX_CURSOR_IBEAM: int
MLX_CURSOR_CROSSHAIR: int
MLX_CURSOR_HAND: int
MLX_CURSOR_HRESIZE: int
MLX_CURSOR_VRESIZE: int
MLX_MOUSE_NORMAL: int
MLX_MOUSE_HIDDEN: int
MLX_MOUSE_DISABLED: int
MLX_MOUSE_BUTTON_LEFT: int
MLX_MOUSE_BUTTON_RIGHT: int
MLX_MOUSE_BUTTON_MIDDLE: int
MLX_SHIFT: int
MLX_CONTROL: int
MLX_ALT: int
MLX_SUPERKEY: int
MLX_CAPSLOCK: int
MLX_NUMLOCK: int
MLX_RELEASE: int
MLX_PRESS: int
MLX_REPEAT: int
MLX_STRETCH_IMAGE: Incomplete
MLX_FULLSCREEN: Incomplete
MLX_MAXIMIZED: Incomplete
MLX_DECORATED: Incomplete
MLX_HEADLESS: Incomplete
MLX_SETTINGS_MAX: Incomplete

class mlx_instance_t(ctypes.Structure):
    x: int
    y: int
    z: int
    enabled: bool

class mlx_image_t(ctypes.Structure):
    width: int
    height: int
    instances: ctypes.Array[mlx_instance_t]

class mlx_t(ctypes.Structure): ...
class mlx_texture_t(ctypes.Structure):
    width: int
    height: int
    bytes_per_pixel: int
    pixels: ctypes.Array[ctypes.c_uint8]

class xpm_t(ctypes.Structure): ...
class mlx_key_data_t(ctypes.Structure):
    key: int
    action: int
    modifier: int

mlx_scrollfunc: Incomplete
mlx_mousefunc: Incomplete
mlx_cursorfunc: Incomplete
mlx_keyfunc: Incomplete
mlx_resizefunc: Incomplete
mlx_closefunc: Incomplete
mlx_loop_hook_func: Incomplete

class _MlxLib:
    def mlx_init(self, width: int, height: int, title: bytes, resize: bool) -> ctypes.POINTER(mlx_t): ...
    def mlx_new_image(self, mlx: ctypes.POINTER(mlx_t), width: int, height: int) -> ctypes.POINTER(mlx_image_t): ...
    def mlx_image_to_window(self, mlx: ctypes.POINTER(mlx_t), img: ctypes.POINTER(mlx_image_t), x: int, y: int) -> int: ...
    def mlx_put_pixel(self, img: ctypes.POINTER(mlx_image_t), x: int, y: int, color: int) -> None: ...
    def mlx_delete_image(self, mlx: ctypes.POINTER(mlx_t), img: ctypes.POINTER(mlx_image_t)) -> None: ...
    def mlx_loop(self, mlx: ctypes.POINTER(mlx_t)) -> None: ...
    def mlx_loop_hook(self, mlx: ctypes.POINTER(mlx_t), fn: Incomplete, param: ctypes.c_void_p) -> None: ...
    def mlx_key_hook(self, mlx: ctypes.POINTER(mlx_t), fn: Incomplete, param: ctypes.c_void_p | None) -> None: ...
    def mlx_close_window(self, mlx: ctypes.POINTER(mlx_t)) -> None: ...
    def mlx_terminate(self, mlx: ctypes.POINTER(mlx_t)) -> None: ...
    def mlx_is_key_down(self, mlx: ctypes.POINTER(mlx_t), key: int) -> bool: ...
    def mlx_load_png(self, path: bytes) -> ctypes.POINTER(mlx_texture_t): ...
    def mlx_texture_to_image(self, mlx: ctypes.POINTER(mlx_t), texture: ctypes.POINTER(mlx_texture_t)) -> ctypes.POINTER(mlx_image_t): ...
    def mlx_delete_texture(self, texture: ctypes.POINTER(mlx_texture_t)) -> None: ...
    def mlx_set_setting(self, setting: Incomplete, value: bool) -> None: ...
    def mlx_get_time(self) -> float: ...

mlx: _MlxLib
