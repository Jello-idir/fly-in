import tkinter


def main():
    # Create the main window
    root = tkinter.Tk()
    root.title("Circle Example")

    # Create a canvas widget to draw on
    canvas = tkinter.Canvas(root, width=400, height=400)
    canvas.pack()

    # Define the center and radius of the circle
    center_x = 200
    center_y = 200
    radius = 100

    # Draw a circle on the canvas
    canvas.create_oval(center_x - radius, center_y - radius, center_x + radius, center_y + radius, fill="blue")

    # Start the Tkinter event loop
    root.mainloop()


if __name__ == "__main__":
    main()
