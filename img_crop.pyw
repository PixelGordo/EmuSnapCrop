#!/usr/bin/env python
# -*- coding: utf-8 -*-

import random
import sys

from PIL import Image

import Tkinter
import tkMessageBox
import tkFileDialog

from libs import files
from libs import tkinter_extra


# How to  keep the parent window with auto-resize
# http://stackoverflow.com/questions/8997497/what-controls-automated-window-resizing-in-tkinter

# CONSTANTS
#=======================================================================================================================
u_PROG_NAME = u'EmuSnap Crop v1.0'


# HELPER FUNCTIONS
#=======================================================================================================================
def is_rect_color(pti_color=(0, 0, 0), po_img=None, pti_nw=(0, 0), pti_se=(0, 0), pi_scans=1):
    """
    Function to get the colors of some random points inside a rectangle defined by pti_pos_1 and pti_pos_2.

    :param po_img: PIL image object.

    :param pti_nw: Top-left corner of the rectangle. i.e. (0, 10)

    :param pti_se: Bottom-right corner of the rectangle. i.e. (100, 20)

    :param pi_scans: Number of scan points.

    :param pti_color: Tuple with RGB values (not sure if it's 0-100 or 0-255)

    :return: A set of tuples with the RGB values for each point.
    """
    lti_colors = []

    for i in range(pi_scans):
        ti_point = (random.randint(pti_nw[0], pti_se[0]), random.randint(pti_nw[1], pti_se[1]))
        ti_color = po_img.getpixel(ti_point)
        lti_colors.append(ti_color)

    sti_colors = set(lti_colors)

    if len(sti_colors) == 1 and pti_color in sti_colors:
        b_is_rect_color = True
    else:
        b_is_rect_color = False

    return b_is_rect_color


# CLASSES
# ======================================================================================================================
class ProgramStatus(object):
    """
    Class to store the status of the program.
    """
    def __init__(self):
        self.b_top = True                           # Top crop active/inactive
        self.b_bottom = True                        # Bottom crop active/inactive
        self.b_left = True                          # Left crop active/inactive
        self.b_right = True                         # Right crop active/inactive
        self.i_crop = 0                             # Number of pixels to crop
        self.i_zoom = 2                             # Zoom multiplier (1, 2, 3 should be enough)
        self._lu_colors = [u'#000000', u'#ff0000',
                           u'#000000', u'#00ff00',
                           u'#000000', u'#0000ff',
                           u'#000000', u'#ff00aa',
                           u'#000000', u'#ffffff']  # Background and Foreground color pairs
        self._i_colors = 0
        self.u_bg_color = self._lu_colors[0]
        self.u_fg_color = self._lu_colors[1]

        self._ti_image_size = (0, 0)
        self._i_image = None
        self._lo_images_fp = []

    def __str__(self):
        u_output = u'<ProgramStatus>\n'
        u_output += u'  .b_top:      %s\n' % self.b_top
        u_output += u'  .b_bottom:   %s\n' % self.b_bottom
        u_output += u'  .b_left:     %s\n' % self.b_left
        u_output += u'  .b_right:    %s\n' % self.b_right
        u_output += u'  .i_crop:     %s\n' % self.i_crop
        u_output += u'  .i_zoom:     %s\n' % self.i_zoom
        u_output += u'  .u_bg_color: %s\n' % self.u_bg_color
        u_output += u'  .u_fg_color: %s\n' % self.u_fg_color

        o_img_fp = self.o_image_fp
        if o_img_fp:
            u_text = u'<FilePath %s/%i %s>' % (str(self._i_image + 1), len(self._lo_images_fp), o_img_fp.u_path)
        else:
            u_text = u'None'

        u_output += u'  .o_img_fp:   %s\n' % u_text
        return u_output.encode('utf8')

    def _reset_crop(self):
        self.i_crop = 0
        self.b_top = True
        self.b_bottom = True
        self.b_left = True
        self.b_right = True

    def switch_border(self, pu_border):

        if self.i_crop:
            if pu_border == 'top' and self.i_crop:
                self.b_top = not self.b_top

            elif pu_border == 'bottom' and self.i_crop:
                self.b_bottom = not self.b_bottom

            elif pu_border == 'left' and self.i_crop:
                self.b_left = not self.b_left

            elif pu_border == 'right' and self.i_crop:
                self.b_right = not self.b_right

            else:
                raise ValueError

        # As an extra of usability, when all borders are off, self.i_crop resets to 0 and all crops are on (but empty)
        if True not in (self.b_top, self.b_bottom, self.b_left, self.b_right):
            self._reset_crop()

    def crop_add(self, pi_value=1):

        # Usability: Can't increase crop size when everything is already selected.
        if self.b_left and self.b_right:
            i_max_x = int(0.5 * self._ti_image_size[0])
        else:
            i_max_x = self._ti_image_size[0]

        if self.b_top and self.b_bottom:
            i_max_y = int(0.5 * self._ti_image_size[1])
        else:
            i_max_y = self._ti_image_size[1]

        if True not in (self.b_top, self.b_bottom):
            i_max = i_max_x
        elif True not in (self.b_left, self.b_right):
            i_max = i_max_y
        else:
            i_max = min(i_max_x, i_max_y)

        # 1st we add/subtract 1 pixel.
        self.i_crop += pi_value

        # 2nd we impose the previously calculated usability limits.
        if self.i_crop <= 0:
            self.i_crop = 0
            self.b_top = True
            self.b_bottom = True
            self.b_left = True
            self.b_right = True
        elif self.i_crop > i_max:
            self.i_crop = i_max

    def zoom_cycle(self):
        """
        Simple method to cycle the zoom level.
        :return: Nothing
        """
        i_max = 3

        self.i_zoom += 1
        if self.i_zoom > i_max:
            self.i_zoom = 1

    def colors_cycle(self):
        """
        Method to cycle foreground and background colors between the available pairs.
        :return: Nothing
        """
        self._i_colors += 2

        if self._i_colors > (len(self._lu_colors) - 2):
            self._i_colors = 0

        self.u_bg_color = self._lu_colors[self._i_colors]
        self.u_fg_color = self._lu_colors[self._i_colors + 1]

    def add_image_fp(self, po_image_fp):
        """
        Method to add images to the list of images to open
        :param po_image_fp:
        :return:
        """
        lu_valid_exts = [u'jpg', u'png']
        if po_image_fp.is_file() and po_image_fp.has_exts(*lu_valid_exts):
            self._lo_images_fp.append(po_image_fp)
            if not self._i_image:
                self._i_image = 0

    def _update_img(self):
        """
        Method to update the current image.
        :return:
        """
        o_img = Image.open(self.o_image_fp.u_path)
        o_img = o_img.convert('RGB')

        # We obtain the dimensions of the image
        self._ti_image_size = o_img.size

        # And also an initial detection of borders
        # TODO: Make it work with more than one border color (opposite corners? one for each side?)
        ti_corner_color = o_img.getpixel((0, 0))

        i_max_pixels = 16

        # ...top border
        i_border_top = 0
        for i in range(i_max_pixels):
            ti_tl_corner = (0, i)
            ti_br_corner = (self._ti_image_size[0] - 1, i)
            if is_rect_color(pti_color=ti_corner_color,
                             po_img=o_img,
                             pti_nw=ti_tl_corner, pti_se=ti_br_corner, pi_scans=16):
                i_border_top += 1
            else:
                break

        # ...bottom border
        i_border_bottom = 0
        for i in range(i_max_pixels):
            ti_tl_corner = (0, self._ti_image_size[1] - 1 - i)
            ti_br_corner = (self._ti_image_size[0] - 1, self._ti_image_size[1] - 1 - i)
            if is_rect_color(pti_color=ti_corner_color,
                             po_img=o_img,
                             pti_nw=ti_tl_corner, pti_se=ti_br_corner, pi_scans=16):
                i_border_bottom += 1
            else:
                break

        # ...left border
        i_border_left = 0
        for i in range(i_max_pixels):
            ti_tl_corner = (i, i_border_top)
            ti_br_corner = (i, self._ti_image_size[1] - i_border_bottom - 1)
            if is_rect_color(pti_color=ti_corner_color,
                             po_img=o_img,
                             pti_nw=ti_tl_corner, pti_se=ti_br_corner, pi_scans=16):
                i_border_left += 1
            else:
                break

        # ...right border
        i_border_right = 0
        for i in range(i_max_pixels):
            ti_tl_corner = (self._ti_image_size[0] - i - 1, i_border_top)
            ti_br_corner = (self._ti_image_size[0] - i - 1, self._ti_image_size[1] - i_border_bottom - 1)
            if is_rect_color(pti_color=ti_corner_color,
                             po_img=o_img,
                             pti_nw=ti_tl_corner, pti_se=ti_br_corner, pi_scans=16):
                i_border_right += 1
            else:
                break

        # Setting the borders
        li_borders = []

        if i_border_top:
            self.b_top = True
            li_borders.append(i_border_top)
        else:
            self.b_top = False

        if i_border_bottom:
            self.b_bottom = True
            li_borders.append(i_border_bottom)
        else:
            self.b_bottom = False

        if i_border_left:
            self.b_left = True
            li_borders.append(i_border_left)
        else:
            self.b_left = False

        if i_border_right:
            self.b_right = True
            li_borders.append(i_border_right)
        else:
            self.b_right = False

        # Typically, the systems I want to process have 8 extra pixels so I'll
        if li_borders:
            self.i_crop = min(li_borders) - min(li_borders) % 8
        else:
            self.i_crop = 0

        # When the crop is zero, all the borders are activated for usability reasons. Since that usability feature is
        # already implemented into "crop_add" method, a quick workaround to apply them is to increment the crop zero
        # pixels.
        self.crop_add(pi_value=0)

    def next_img(self):
        """
        Method to activate the next image.
        :return: Nothing
        """

        i_new_image = self._i_image + 1

        if len(self._lo_images_fp) == 0:
            i_new_image = None
        elif i_new_image >= len(self._lo_images_fp):
            i_new_image = 0

        if i_new_image != self._i_image:
            self._i_image = i_new_image
            self._update_img()

    def _get_i_imgs(self):
        return len(self._lo_images_fp)

    def _get_i_img(self):
        return self._i_image

    i_img = property(fget=_get_i_img, fset=None)
    i_imgs = property(fget=_get_i_imgs, fset=None)

    def prev_img(self):
        """
        Method to activate the previous image.
        :return: Nothing
        """
        i_new_image = self._i_image - 1

        if len(self._lo_images_fp) == 0:
            i_new_image = None
        elif i_new_image < 0:
            i_new_image = len(self._lo_images_fp) - 1

        if i_new_image != self._i_image:
            self._i_image = i_new_image
            self._update_img()

    def _get_image_fp(self):
        """
        Method to get the current active image_fp.

        :return: The current active image_fp
        """
        if self._i_image is None:
            o_img_fp = None
        else:
            o_img_fp = self._lo_images_fp[self._i_image]

        return o_img_fp

    def _get_image_size(self):
        """
        Method to get the current image size.

        :return: The current image size. i.e. (320, 240)
        """
        return self._ti_image_size

    o_image_fp = property(fset=None, fget=_get_image_fp)
    ti_image_size = property(fset=None, fget=_get_image_size)


class ControlsFrame:
    """
    Class to store the frame with the controls.
    """
    def __init__(self, po_window, po_status):
        """

        :param po_window:
        :type po_status: ProgramStatus
        :return:
        """
        # Some widgets' text need encoding so it's cleaner having them here.
        u_top_text = u'⬒'.encode('utf8')
        u_bot_text = u'⬓'.encode('utf8')
        u_left_text = u'◧'.encode('utf8')
        u_right_text = u'◨'.encode('utf8')
        u_color_text = u'color'.encode('utf8')
        u_zoom_text = u'zoom'
        u_plus_text = u'+'.encode('utf8')
        u_less_text = u'-'.encode('utf8')

        self._o_var_top = Tkinter.BooleanVar()
        self._o_var_bottom = Tkinter.BooleanVar()
        self._o_var_left = Tkinter.BooleanVar()
        self._o_var_right = Tkinter.BooleanVar()
        self._o_var_crop = Tkinter.StringVar()
        self._o_img = Tkinter.StringVar()
        self._o_var_file = Tkinter.StringVar()
        self._o_var_size_src = Tkinter.StringVar()
        self._o_var_size_dst = Tkinter.StringVar()

        # Top Frame
        #==========
        self._o_frame_top = Tkinter.Frame(master=po_window, bd=0, relief=Tkinter.GROOVE, borderwidth=2, padx=4, pady=4)
        self._o_frame_top.pack(fill=Tkinter.X, padx=5, pady=5)
        self._o_frame_top.columnconfigure(4, weight=3)
        self._o_frame_top.columnconfigure(8, weight=3)

        self._o_check_up = Tkinter.Checkbutton(master=self._o_frame_top, text=u_top_text, variable=self._o_var_top,
                                               onvalue=True, offvalue=False, width=0, command=_ctrl_switch_crop_top)
        self._o_check_up.grid(row=0, column=1)

        self._o_check_down = Tkinter.Checkbutton(master=self._o_frame_top, text=u_bot_text,
                                                 variable=self._o_var_bottom, onvalue=True, offvalue=False,
                                                 command=_ctrl_switch_crop_bottom)
        self._o_check_down.grid(row=2, column=1)

        self._o_check_left = Tkinter.Checkbutton(master=self._o_frame_top, text=u_left_text, variable=self._o_var_left,
                                                 onvalue=True, offvalue=False, command=_ctrl_switch_crop_left)
        self._o_check_left.grid(row=1, column=0)

        self._o_check_right = Tkinter.Checkbutton(master=self._o_frame_top, text=u_right_text,
                                                  variable=self._o_var_right, onvalue=True, offvalue=False,
                                                  command=_ctrl_switch_crop_right)
        self._o_check_right.grid(row=1, column=2)

        self._o_button_color = Tkinter.Button(master=self._o_frame_top, text=u_color_text, width=3,
                                              command=_ctrl_colors_cycle)
        self._o_button_color.grid(row=0, column=6)

        self._o_button_zoom = Tkinter.Button(master=self._o_frame_top, text=u_zoom_text, width=3,
                                             command=_ctrl_zoom_cycle)
        self._o_button_zoom.grid(row=2, column=6)

        self._o_button_less = Tkinter.Button(master=self._o_frame_top, text=u_less_text, width=1,
                                             command=_ctrl_crop_dec)
        self._o_button_less.grid(row=1, column=5)

        self._o_label_crop = Tkinter.Label(master=self._o_frame_top, textvar=self._o_var_crop)
        self._o_label_crop.grid(row=1, column=6)

        self._o_button_more = Tkinter.Button(master=self._o_frame_top, text=u_plus_text, width=0,
                                             command=_ctrl_crop_inc)
        self._o_button_more.grid(row=1, column=7)

        self._o_button_prev_img = Tkinter.Button(master=self._o_frame_top, text=u'◀', command=_ctrl_prev_img)
        self._o_button_prev_img.grid(row=1, column=9)

        self._o_button_save_img = Tkinter.Button(master=self._o_frame_top, text=u'save',
                                                 command=_ctrl_save_with_confirmation)
        self._o_button_save_img.grid(row=0, column=10)

        self._o_label_img = Tkinter.Label(master=self._o_frame_top, textvar=self._o_img)
        self._o_label_img.grid(row=1, column=10)

        self._o_button_next_img = Tkinter.Button(master=self._o_frame_top, text=u'▶', command=_ctrl_next_img)
        self._o_button_next_img.grid(row=1, column=11)

        # Bottom Frame
        #=============
        self._o_frame_bottom = Tkinter.Frame(master=po_window, relief=Tkinter.GROOVE,
                                             borderwidth=2, padx=4, pady=4)
        self._o_frame_bottom.pack(fill=Tkinter.X, padx=5, pady=5)
        self._o_frame_bottom.columnconfigure(1, weight=3)

        # Bottom section
        #---------------
        self._o_label_file = Tkinter.Label(master=self._o_frame_bottom, textvar=self._o_var_file, anchor=Tkinter.CENTER)
        self._o_label_file.grid(row=0, column=0, columnspan=3)

        self._o_label_src_size = Tkinter.Label(master=self._o_frame_bottom, textvar=self._o_var_size_src)
        self._o_label_src_size.grid(row=1, column=0, columnspan=1, sticky='w')

        self._o_label_dst_size = Tkinter.Label(master=self._o_frame_bottom, textvar=self._o_var_size_dst)
        self._o_label_dst_size.grid(row=1, column=2, columnspan=1, sticky='w')

        # Hover tips for widgets
        #-----------------------
        self._o_tip_top = tkinter_extra.ToolTip(self._o_check_up, text=u'[w] Top crop ON/OFF', delay=500)
        self._o_tip_bottom = tkinter_extra.ToolTip(self._o_check_down, text=u'[s] Bottom crop ON/OFF', delay=500)
        self._o_tip_left = tkinter_extra.ToolTip(self._o_check_left, text=u'[a] Left crop ON/OFF', delay=500)
        self._o_tip_right = tkinter_extra.ToolTip(self._o_check_right, text=u'[d] Right crop ON/OFF', delay=500)

        self._o_tip_color = tkinter_extra.ToolTip(self._o_button_color, text=u'[c] Change crop indicator color',
                                                  delay=500)
        self._o_tip_zoom = tkinter_extra.ToolTip(self._o_button_zoom, text=u'[z] Change zoom (1x, 2x, 3x)', delay=500)

        self._o_tip_inc_crop = tkinter_extra.ToolTip(self._o_button_more, text=u'[+] Increase crop size', delay=500)
        self._o_tip_dec_crop = tkinter_extra.ToolTip(self._o_button_less, text=u'[-] Reduce crop size', delay=500)

        self._o_tip_next = tkinter_extra.ToolTip(self._o_button_next_img, text=u'[▶] Next image', delay=500)
        self._o_tip_prev = tkinter_extra.ToolTip(self._o_button_prev_img, text=u'[◀] Previous image', delay=500)

        self._o_tip_save = tkinter_extra.ToolTip(self._o_button_save_img, text=u'[ctrl-s] Save image', delay=500)

        self.update(po_status)

    def update(self, po_status):
        """
        Method to update the status of the control panel based on the internal ProgramStatus
        :type po_status: ProgramStatus
        :return: Nothing
        """

        # The checkboxes status are updated accordingly the internal status of the program
        self._o_var_top.set(po_status.b_top)
        self._o_var_bottom.set(po_status.b_bottom)
        self._o_var_left.set(po_status.b_left)
        self._o_var_right.set(po_status.b_right)

        # Now updating the crop label
        self._o_var_crop.set(u'%s px' % po_status.i_crop)
        if po_status.i_img:
            self._o_img.set(u'%i / %i' % (po_status.i_img + 1, po_status.i_imgs))
        else:
            self._o_img.set(u'0 / %i' % po_status.i_imgs)

        if po_status.o_image_fp:
            self._o_var_file.set(u'Image: %s' % po_status.o_image_fp.u_path)
        else:
            self._o_var_file.set(u'Image: None')

        # Image information
        #------------------
        if po_status.ti_image_size[0] and po_status.ti_image_size[1]:
            u_src_size = u'Orig. size: %ix%i (%.2f)' % (po_status.ti_image_size[0],
                                                        po_status.ti_image_size[1],
                                                        float(po_status.ti_image_size[0]) / po_status.ti_image_size[1])
        else:
            u_src_size = u'Orig. size: %ix%i (---)' % (po_status.ti_image_size[0], po_status.ti_image_size[1])

        self._o_var_size_src.set(u_src_size)

        i_hor_sides = 0
        if po_status.b_left:
            i_hor_sides += 1
        if po_status.b_right:
            i_hor_sides += 1

        i_ver_sides = 0
        if po_status.b_top:
            i_ver_sides += 1
        if po_status.b_bottom:
            i_ver_sides += 1

        ti_final_size = (po_status.ti_image_size[0] - i_hor_sides * po_status.i_crop,
                         po_status.ti_image_size[1] - i_ver_sides * po_status.i_crop)
        if ti_final_size[1]:
            u_final_aspect = u'%.2f' % (float(ti_final_size[0]) / ti_final_size[1])
        else:
            u_final_aspect = u'---'

        u_dst_size = u'Final size: %sx%s (%s)' % (ti_final_size[0], ti_final_size[1], u_final_aspect)
        self._o_var_size_dst.set(u_dst_size)


class ImgCanvas:
    """
    Class to store the canvas where the screenshot and the cropping boxes are drawn.
    """
    def __init__(self, o_window):

        self._i_crop = 0
        self._i_zoom = 0
        self._ti_size = (0, 0)
        self._o_image_fp = None
        self._u_fg_color = u'#ff00ff'

        self._o_canvas = Tkinter.Canvas(o_window,
                                        borderwidth=0, highlightthickness=0, bd=0,
                                        width=self._ti_size[0], height=self._ti_size[1],
                                        bg='black')

        # Canvas objects
        #---------------
        # There is a problem when placing images into a canvas. Basically you need to keep "alive" the "raw" PhotoImage
        # and then, you have another pointer for the image placed into your canvas. Another problem is we need to go
        # back and forth with the zoom level. So, we always need to keep the original 1:1 image which will be then
        # later manipulated (zoomed in)
        self._o_orig_image = Tkinter.PhotoImage(file=u'')
        self._o_zoom_image = None
        self._o_canv_image = self._o_canvas.create_image(0, 0, anchor=Tkinter.NW, image=self._o_zoom_image)

        self._to_crop_rectangles = [self._o_canvas.create_rectangle(0, 0, 0, 0,
                                                                    fill='red', width=0, stipple='gray50'),
                                    self._o_canvas.create_rectangle(0, 0, 0, 0,
                                                                    fill='green', width=0, stipple='gray50'),
                                    self._o_canvas.create_rectangle(0, 0, 0, 0,
                                                                    fill='blue', width=0, stipple='gray50'),
                                    self._o_canvas.create_rectangle(0, 0, 0, 0,
                                                                    fill='yellow', width=0, stipple='gray50')]
        self._o_canvas.pack()

        self._place_crop_rects()

    def _place_crop_rects(self, pi_crop=0, pb_top=True, pb_bottom=True, pb_left=True, pb_right=True):
        """
        Method to modify the crop dimensions.
        """

        # The scheme of the crops is more or less like:
        #
        #     TTTTTTTTTTTTTTTTTTTTTTT
        #     L                     R
        #     L                     R
        #     L                     R
        #     L                     R
        #     L                     R
        #     BBBBBBBBBBBBBBBBBBBBBBB
        #
        # And we always set the coordinates of the rectangles from the top-left corner to the bottom-right one.
        #
        # It seems that there is a problem or weird thing when defining rectangle coordinates where the second x,y pair
        # is shorter by ONE pixel so I have to manually add it.

        # 1st, we calculate the crop of each side
        #----------------------------------------
        i_crop_top = 0
        if pb_top:
            i_crop_top = pi_crop

        i_crop_bottom = 0
        if pb_bottom:
            i_crop_bottom = pi_crop

        i_crop_left = 0
        if pb_left:
            i_crop_left = pi_crop

        i_crop_right = 0
        if pb_right:
            i_crop_right = pi_crop

        # 2nd, we set the coordinates of each of the 4 rectangles on the canvas
        #----------------------------------------------------------------------

        # Top rectangle
        self._o_canvas.coords(self._to_crop_rectangles[0],
                              0, -1,
                              self._ti_size[0], i_crop_top)

        # Bottom rectangle
        self._o_canvas.coords(self._to_crop_rectangles[1],
                              0, self._ti_size[1] - i_crop_bottom,
                              self._ti_size[0], self._ti_size[1])

        # Left rectangle
        self._o_canvas.coords(self._to_crop_rectangles[2],
                              -1, i_crop_top,
                              i_crop_left, self._ti_size[1] - i_crop_bottom)

        # Right rectangle
        self._o_canvas.coords(self._to_crop_rectangles[3],
                              self._ti_size[0] - i_crop_right, i_crop_top,
                              self._ti_size[0], self._ti_size[1] - i_crop_bottom)

    # WIP
    def update(self, po_prog_status):
        """
        Method to update the "visual" frame depending on the current internal status of the program.
        :type po_prog_status: ProgramStatus
        :return:
        """
        # Crop update
        i_crop = po_prog_status.i_crop * po_prog_status.i_zoom
        if self._i_crop != i_crop:
            self._update_crop(po_prog_status)

        # Image update
        if self._o_image_fp != po_prog_status.o_image_fp:
            self._update_image(po_prog_status)
            self._update_canvas_size(po_prog_status)
            self._update_crop(po_prog_status)

        # Zoom update
        if self._i_zoom != po_prog_status.i_zoom:
            self._update_zoom(po_prog_status)
            self._update_canvas_size(po_prog_status)
            self._update_crop(po_prog_status)

        # Crop bars color update
        if self._u_fg_color != po_prog_status.u_fg_color:
            self._update_colors(po_prog_status)

        # Update canvas size
        ti_size = (po_prog_status.ti_image_size[0] * po_prog_status.i_zoom,
                   po_prog_status.ti_image_size[1] * po_prog_status.i_zoom)
        if self._ti_size != ti_size:
            self._update_canvas_size(po_prog_status)
            self._update_crop(po_prog_status)

    def _update_image(self, po_prog_status):
        """
        Method to update the image of the canvas.
        :type po_prog_status: ProgramStatus
        :return: Nothing
        """

        # The _update_image method is a bit "messy" since we need to update a couple of elements:
        #
        #   1. The FilePath object containing the path of the image.
        #   2. The Tkinter raw or "texture" image that will be painted somewhere.
        #   3. The raw image already painted onto the canvas.
        self._o_image_fp = po_prog_status.o_image_fp

        if self._o_image_fp:
            self._o_orig_image = Tkinter.PhotoImage(file=self._o_image_fp.u_path)
            # Luckily, Tkinter only accepts integer zooms and the result is not dithered
            self._o_zoom_image = self._o_orig_image.zoom(po_prog_status.i_zoom)
            self._o_canvas.itemconfig(self._o_canv_image, image=self._o_zoom_image)

            #self._update_canvas_size(po_prog_status)

    def _update_crop(self, po_prog_status):
        """
        Method to update the crop.
        :type po_prog_status: ProgramStatus
        :return: Nothing
        """

        i_crop = po_prog_status.i_crop * po_prog_status.i_zoom

        self._place_crop_rects(pi_crop=i_crop,
                               pb_top=po_prog_status.b_top, pb_bottom=po_prog_status.b_bottom,
                               pb_left=po_prog_status.b_left, pb_right=po_prog_status.b_right)

    def _update_colors(self, po_prog_status):
        """
        Method to update the background and foreground colors.
        :type po_prog_status: ProgramStatus
        :return: Nothing
        """
        for o_rect in self._to_crop_rectangles:
            self._o_canvas.itemconfig(o_rect, fill=po_prog_status.u_fg_color)

    def _update_zoom(self, po_prog_status):
        """
        Method to update the zoom level
        :param po_prog_status:
        :return:
        """
        self._o_zoom_image = self._o_orig_image.zoom(po_prog_status.i_zoom)
        self._o_canvas.itemconfig(self._o_canv_image, image=self._o_zoom_image)

    def _update_canvas_size(self, po_prog_status):
        """
        Simple method to update the canvas size.
        :type po_prog_status: ProgramStatus
        :return: Nothing
        """
        # 1st we resize the canvas itself
        self._ti_size = (self._o_zoom_image.width(), self._o_zoom_image.height())
        self._o_canvas.config(width=self._ti_size[0], height=self._ti_size[1])
        # 2nd we need to resize and reposition the crop bars
        self._update_crop(po_prog_status)


# CONTROL FUNCTIONS
# ======================================================================================================================
def _ctrl_switch_crop_top(event=None):
    global o_program_status
    global o_img_canvas
    global o_ctrl_frame

    # 1st we update the internal status of the program
    o_program_status.switch_border('top')

    # 2nd we cascade the status to the visual elements to reflect the changes
    o_img_canvas.update(o_program_status)
    o_ctrl_frame.update(o_program_status)


def _ctrl_switch_crop_bottom(event=None):
    global o_program_status
    global o_img_canvas
    global o_ctrl_frame

    o_program_status.switch_border('bottom')

    o_img_canvas.update(o_program_status)
    o_ctrl_frame.update(o_program_status)


def _ctrl_switch_crop_left(event=None):
    global o_program_status
    global o_img_canvas
    global o_ctrl_frame

    o_program_status.switch_border('left')

    o_img_canvas.update(o_program_status)
    o_ctrl_frame.update(o_program_status)


def _ctrl_switch_crop_right(event=None):
    global o_program_status
    global o_img_canvas
    global o_ctrl_frame

    o_program_status.switch_border('right')

    o_img_canvas._update_crop(o_program_status)
    o_ctrl_frame.update(o_program_status)


def _ctrl_crop_inc(event=None):
    global o_program_status
    global o_img_canvas
    global o_ctrl_frame

    # 1st we update the internal status of the program
    o_program_status.crop_add()

    # 2nd we cascade that status to the visual elements
    o_img_canvas.update(o_program_status)
    o_ctrl_frame.update(o_program_status)


def _ctrl_crop_inc_jump(event=None):
    """
    To increase the crop in jumps of 8 pixels
    :param event:
    :return: Nothing
    """
    global o_program_status
    global o_img_canvas
    global o_ctrl_frame

    # 1st we update the internal status of the program
    o_program_status.crop_add(pi_value=8)

    # 2nd we cascade the updated status to the visual elements
    o_img_canvas.update(o_program_status)
    o_ctrl_frame.update(o_program_status)


def _ctrl_crop_dec_jump(event=None):
    """
    To increase the crop in jumps of 8 pixels
    :param event:
    :return: Nothing
    """
    global o_program_status
    global o_img_canvas
    global o_ctrl_frame

    # 1st we update the program status
    o_program_status.crop_add(pi_value=-8)

    # 2nd we cascade that status to the visual elements
    o_img_canvas.update(o_program_status)
    o_ctrl_frame.update(o_program_status)


def _ctrl_crop_dec(event=None):
    global o_program_status
    global o_img_canvas
    global o_ctrl_frame

    o_program_status.crop_add(pi_value=-1)

    o_img_canvas._update_crop(o_program_status)
    o_ctrl_frame.update(o_program_status)


def _ctrl_zoom_cycle(event=None):
    global o_program_status
    global o_img_canvas
    global o_ctrl_frame

    # 1st we update the internal status of the program
    o_program_status.zoom_cycle()

    # 2nd we send that status to the proper GUI elements to update them
    o_img_canvas.update(o_program_status)
    o_ctrl_frame.update(o_program_status)


def _ctrl_colors_cycle(event=None):
    global o_program_status
    global o_img_canvas
    global o_ctrl_frame

    # 1st we update the interla status of the program
    o_program_status.colors_cycle()

    # 2nd we "cascade" that status to the visual elements
    o_img_canvas.update(o_program_status)
    o_ctrl_frame.update(o_program_status)


def _ctrl_close(event):
    sys.exit()


def _ctrl_save_with_confirmation(event=None):
    global o_main_window
    global o_program_status
    global o_img_canvas
    global o_ctrl_frame

    # 1st we open the confirmation dialog
    b_overwrite = tkMessageBox.askyesno(u'Overwrite the original image?')

    if b_overwrite:
        _ctrl_save(event)


def _ctrl_save(event=None):
    """
    Function to save the cropped screenshot to disk.
    :param event:
    :return: Nothing.
    """
    global o_program_status
    global o_img_canvas
    global o_ctrl_frame

    # 1st we save the file
    if o_program_status.i_crop > 0:
        o_src_img = Image.open(o_program_status.o_image_fp.u_path, 'r')
        ti_img_size = o_src_img.size

        if o_program_status.b_top:
            i_crop_n = o_program_status.i_crop
        else:
            i_crop_n = 0

        if o_program_status.b_bottom:
            i_crop_s = ti_img_size[1] - o_program_status.i_crop
        else:
            i_crop_s = ti_img_size[1]

        if o_program_status.b_left:
            i_crop_w = o_program_status.i_crop
        else:
            i_crop_w = 0

        if o_program_status.b_right:
            i_crop_e = ti_img_size[0] - o_program_status.i_crop
        else:
            i_crop_e = ti_img_size[0]

        ti_crop = (i_crop_w, i_crop_n, i_crop_e, i_crop_s)

        o_dst_img = o_src_img.crop(ti_crop)
        u_output_file = o_program_status.o_image_fp.u_path
        o_dst_img.save(u_output_file)

        # A quick around to reload the image is to move one image forward and back
        _ctrl_next_img()
        _ctrl_prev_img()


def _ctrl_next_img(event=None):
    global o_program_status
    global o_img_canvas
    global o_ctrl_frame

    # 1st we update the internal status of the program
    o_program_status.next_img()

    # 2nd we send that status to the proper GUI elements to update them
    o_img_canvas.update(o_program_status)
    o_ctrl_frame.update(o_program_status)


def _ctrl_prev_img(event=None):
    global o_program_status
    global o_img_canvas
    global o_ctrl_frame

    # 1st we update the internal status of the program
    o_program_status.prev_img()

    # 2nd we send that status to the proper GUI elements to update them
    o_img_canvas.update(o_program_status)
    o_ctrl_frame.update(o_program_status)


# TODO: Main window is not resizable anymore so MAYBE this function can be removed.
def _ctrl_resize(event):
    """
        Control function to make main window auto-resizable.

        While the main window size configuration is empty, it's auto-resizable. But every time you change the size of the
        window manually, actually you are setting a fixed size. To avoid it, when resizing the window, this function is
        called to delete the fixed size making the window auto-resizable again.

        :param event:
        :return:
        """
    global o_main_window
    o_main_window.wm_geometry('')


# MAIN CODE
#=======================================================================================================================

# Initialization
#---------------
o_program_status = ProgramStatus()

# Creating and starting the GUI
#------------------------------
o_main_window = Tkinter.Tk()
o_main_window.wm_title(u_PROG_NAME)
o_main_window.wm_minsize(width=320, height=0)
o_main_window.resizable(0, 0)

o_img_canvas = ImgCanvas(o_main_window)
o_ctrl_frame = ControlsFrame(o_main_window, o_program_status)

try:
    u_arg = sys.argv[1].decode('utf8')
except IndexError:
    u_arg = tkFileDialog.askopenfilename(master=o_main_window,
                                         title=u'EmuSnap Crop v1.0 - Open image',
                                         defaultextension=u'png',
                                         filetypes=[("Description 1", "*.png"), ("Description 2", "*.jpg")])

# TODO: Exit program when u_arg = empty or current dir doesn't have images. Usability: when no images present, leave
# program open but showing 0 / 0 images
if not u_arg:
    sys.exit()

o_arg_fp = files.FilePath(u_arg)

# Standard process
#-----------------
lo_files_fp = []

if o_arg_fp.is_dir():
    lo_files_fp.extend(o_arg_fp.content(pu_mode='files'))

    for o_file_fp in lo_files_fp:
        o_program_status.add_image_fp(o_file_fp)

elif o_arg_fp.is_file():
    o_root_fp = files.FilePath(o_arg_fp.u_root)
    lo_files_fp.extend(o_root_fp.content(pu_mode='files'))

    for o_file_fp in lo_files_fp:
        o_program_status.add_image_fp(o_file_fp)

    # I don't have a method to directly jump to a particular image so I have to follow this nasty loop...
    while o_program_status.o_image_fp.u_path != o_arg_fp.u_path:
        o_program_status.next_img()

else:
    raise IOError('argument is not a file or a directory')

# Keyboard controls
#------------------
o_main_window.bind('<w>', _ctrl_switch_crop_top)
o_main_window.bind('<s>', _ctrl_switch_crop_bottom)
o_main_window.bind('<a>', _ctrl_switch_crop_left)
o_main_window.bind('<d>', _ctrl_switch_crop_right)
o_main_window.bind('<z>', _ctrl_zoom_cycle)
o_main_window.bind('<c>', _ctrl_colors_cycle)
o_main_window.bind('<Escape>', _ctrl_close)
o_main_window.bind('<Control-s>', _ctrl_save_with_confirmation)
o_main_window.bind('<Control-Shift-KeyPress-S>', _ctrl_save)
o_main_window.bind('<Right>', _ctrl_next_img)
o_main_window.bind('<Left>', _ctrl_prev_img)

o_main_window.bind('<Shift-KP_Add>', _ctrl_crop_inc_jump)
o_main_window.bind('<Shift-KP_Subtract>', _ctrl_crop_dec_jump)
o_main_window.bind('<KP_Add>', _ctrl_crop_inc)
o_main_window.bind('<KP_Subtract>', _ctrl_crop_dec)
# TODO: Add windows and OSX binds for mouse scroll wheel. YES!!! they use different names :/
o_main_window.bind('<Button-4>', _ctrl_crop_inc)            # Linux Mouse scroll wheel up
o_main_window.bind('<Button-5>', _ctrl_crop_dec)            # Linux Mouse scroll wheel down

# Before starting the main loop, I initialize the window with the current status of the program
o_img_canvas.update(o_program_status)
o_ctrl_frame.update(o_program_status)

o_main_window.mainloop()
