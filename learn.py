from MLX.libmlx import *

mlx_ptr = mlx.mlx_init(100, 100, b"title", False)
img = mlx.mlx_new_image(mlx_ptr, 1, 1)

for i in range(img.contents.height):
    for j in range(img.contents.height):
        print("drawing in ", i, j)
        mlx.mlx_put_pixel(img, i, j, 0xffffffff)

mlx.mlx_image_to_window(mlx_ptr, img, 25, 25)
mlx.mlx_loop(mlx_ptr)
