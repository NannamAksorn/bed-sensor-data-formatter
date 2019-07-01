from tkinter import *
from tkinter import filedialog
from tkinter.messagebox import showerror
import numpy as np
import math
import os
import glob
import platform
import subprocess
import shutil

class MyFrame(Frame):
    def __init__(self):
        Frame.__init__(self)
        self.master.title("SEN3 + 264 formatter")
        self.master.minsize(width=300, height=500)
        self.master.rowconfigure(10, weight=1)
        self.master.columnconfigure(10, weight=1)
        self.grid(sticky=W+E+N+S)
        
        self.label = Label(self, text="Press 'Format *' button and select folder that you want to format.\n The result will be inside 'Formatted_sendat' or 'Formatted_video' folder")
        self.label.grid(row=1,column=1)

        self.button = Button(self, text="Format SEN3", command=self.format_SEN3, width=10)
        self.button.grid(row=2, column=1, sticky=W)
        
        # video format
        self.lbl_help_video = Label(self, text="""
        .............................................................
        \nTo format Video please fill in Room number and framerate.\n
        *Try with a single video first to get the correct framerate for each room
        .............................................................
        """)
        self.lbl_help_video.grid(row=3,column=1)
        
        self.lbl_room = Label(self, text="Room Number:")
        self.lbl_room.grid(row=4,column=1,sticky=W)
        vcmd = (self.master.register(self.validate),'%d', '%i', '%P', '%s', '%S', '%v', '%V', '%W')
        self.txt_room = Entry(self, validate = 'key', validatecommand = vcmd)
        self.txt_room.grid(row=5, column=1, sticky=W)
        
        self.lbl_fr = Label(self, text="Frame Rate(5,12):")
        self.lbl_fr.grid(row=6,column=1,sticky=W)
        self.txt_fr = Entry(self, validate = 'key', validatecommand = vcmd)
        self.txt_fr.grid(row=7, column=1, sticky=W)
        
        self.btn_video = Button(self, text="Format Video", command=self.format_video, width=10)
        self.btn_video.grid(row=8, column=1, sticky=W)
        
        self.logBox = Listbox(self,selectmode=EXTENDED)
        self.logBox.grid(row=10, column =1, sticky=EW)
        self.logBox.insert(1,"Log: waiting for action")
        self.logLine = 10000
        
    def validate(self, action, index, value_if_allowed,
                       prior_value, text, validation_type, trigger_type, widget_name):
        if not text or text in '0123456789':
            return True
        else:
            return False

    def format_SEN3(self):
        folder_path = filedialog.askdirectory()
        if folder_path:
            try:
                self.logLine -= 1
                self.logBox.insert(self.logLine, f"SEN3 Formating {folder_path}")
                
                # get all targets
                filenames = glob.glob(os.path.join(folder_path, '*sen3.csv'))
                total = len(filenames)
                count = 0
                
                self.logLine -= 1
                self.logBox.insert(self.logLine, f"Found {total} SEN3_CSV files")

                for filename in filenames:
                    data = []

                    if not os.path.exists(os.path.join(folder_path, 'Formatted_sendat')):
                        self.logLine -= 1
                        self.logBox.insert(self.logLine, f"Create Formatted_sendat folder")
                        os.makedirs(os.path.join(folder_path, 'Formatted_sendat'))

                    # read
                    with open(filename, 'r') as f:
                        next(f)
                        for line in f:
                            lineData = [int(n) for n in line.split(',')]
                            data.extend(lineData)

                    # format
                    formatedData = []
                    for i in range(0, math.floor(len(data)/32)):
                    #     header
                        message = [170, 40, 20, 0, 0, 0, 0, 0, 1, 15]
                        senData = {
                            0: [],
                            1: [],
                            2: [],
                            3: []
                        }
                        for j in range(8):
                            for k in range(4):
                                senData[k].append(data[i*32 + j * 4 + k])
                        for d in range(4):
                            message.extend(senData[d])
                    #         endder
                        message.extend([194,212,165])
                        formatedData.extend(message)
                    formatedData = np.array(formatedData, dtype=np.uint8)

                    # rename
                    rn = os.path.basename(filename).replace('_','')
                    new_filename = f'SEN3_{rn[:12]}_{rn[12:20]}_{rn[20:26]}.sendat'

                    # save
                    with open(os.path.join(folder_path,'Formatted_sendat', new_filename), 'wb') as f:
                        f.write(formatedData.tobytes())
                        count += 1
                        self.logLine -= 1
                        self.logBox.insert(self.logLine, f"{count / total * 100 } %")
                        
                        
                self.logLine -= 1
                self.logBox.insert(self.logLine, f"Completed(SEN3)")
            except:                     # <- naked except is a bad idea
                showerror("Open Source File", "Failed to read file\n'%s'" % fname)
            return
        
    def format_video(self):
        room_no = self.txt_room.get()
        fr = self.txt_fr.get()
        if (not room_no or not fr):
            self.logLine -= 1
            self.logBox.insert(self.logLine, f"Please Enter Room Number and Framerate")
            return
            
        folder_path = filedialog.askdirectory()
        if folder_path:
            try:
                self.logLine -= 1
                self.logBox.insert(self.logLine, f"Video Formating {folder_path}")
                
                self.logLine -= 1
                self.logBox.insert(self.logLine, f"parameters = room:{room_no}, framerate:{fr}")
                
                if not os.path.exists(os.path.join(folder_path, 'Formatted_video')):
                    os.makedirs(os.path.join(folder_path,'Formatted_video'))
                else:
                    shutil.rmtree(os.path.join(folder_path,'Formatted_video'))
                    os.makedirs(os.path.join(folder_path,'Formatted_video'))
                    self.logLine -= 1
                    self.logBox.insert(self.logLine, f"Removed old 'Formatted_video' folder.")
                    
                self.logLine -= 1
                self.logBox.insert(self.logLine, f"Created 'Formatted_video' folder")

                if platform.system() != 'Darwin':
                    ffmpeg = '.\\ffmpeg_win'
                else:
                    ffmpeg = './ffmpeg_mac'
                    
                self.logLine -= 1
                self.logBox.insert(self.logLine, f"running {ffmpeg}")

                filenames = glob.glob(os.path.join(folder_path, '*.264'))
                total = len(filenames)                
                count = 0
                
                self.logLine -= 1
                self.logBox.insert(self.logLine, f"Found {total} .264 files")
                
                for filename in filenames:
                    new_filename = os.path.join(folder_path, 'Formatted_video',f'{room_no}_{os.path.basename(filename)[10:25]}.mp4')
                    subprocess.check_output(f"{ffmpeg} -framerate {fr} -i {filename} -c copy {new_filename}", shell=True)
                    
                    count += 1
                    self.logLine -= 1
                    self.logBox.insert(self.logLine, f"{count / total * 100 } %")                
 
                self.logLine -= 1
                self.logBox.insert(self.logLine, f"Completed(Video)")
            except:                     # <- naked except is a bad idea
                showerror("Open Source File", "Failed to read file\n'%s'" % fname)
            return

if __name__ == "__main__":
    MyFrame().mainloop()
