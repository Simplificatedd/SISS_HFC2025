from tkinter import *
from tkinter import filedialog
import shutil
import os
from CV_parser import CvConverter
import logging

BG = "#84848a"
BG_COLOR = "#020229"
TEXT_COLOR = "#ffffff"

FONT = "Helvetica 12"
FONT_BOLD = "Helvetica 12 bold"

BOT_NAME = "Debbie"
MODEL = "qwen2.5:3b"

CAREER_KEY = "career", "job", "position", "role", "careers", "jobs", "positions", "roles", "work", "employment", "occupation"
SKILL_KEY = "skill", "expertise", "technology", "competency", "skills", "expertises", "technologies", "competencies"

class ChatGUI:
    def __init__(self):
        self.window = Tk()
        self.uploaded_file_label = None
        self.uploaded_file_path = None
        self._setup_main_window()
        self.send_enabled = False

    def run(self):
        self.window.mainloop()

    def _setup_main_window(self):
        self.window.title("Chatbot")
        self.window.configure(bg=BG_COLOR)
        self.window.minsize(350, 450) # Minimum size
        self.window.geometry("550x700") # Size upon opening

        # Header
        header = Label(self.window, bg=BG_COLOR, fg=TEXT_COLOR, text="Welcome", font=FONT_BOLD, pady=10, anchor="center", justify="center")
        header.pack(fill=X)

        # Text widget
        self.text_widget = Text(self.window, bg=BG_COLOR, fg=TEXT_COLOR, font=FONT, padx=5, pady=5)
        self.text_widget.pack(expand=True, fill=BOTH, padx=10, pady=(10, 0))
        self.text_widget.configure(cursor="arrow", state="disabled")

        # Scrollbar
        scrollbar = Scrollbar(self.text_widget)
        scrollbar.pack(side=RIGHT, fill=Y)
        scrollbar.configure(command=self.text_widget.yview)

        # Bottom frame
        bottom_frame = Frame(self.window, bg=BG, height=160)
        bottom_frame.pack(fill=X, side=BOTTOM, pady=10, padx=10)

        # Upload button
        upload_button = Button(bottom_frame, text="Upload CV\n(docx/pdf)", font=FONT_BOLD, bg=BG, command=self._upload_file)  # Triple the height by adding internal padding in y-direction
        upload_button.grid(row=1, column=0, sticky="w", padx=5, ipady=10)

        # message entry box
        self.msg_entry = Text(bottom_frame, bg="#2C3E50", fg=TEXT_COLOR, font=FONT, height=1)  # Set height to match Entry and disable word wrapping
        self.msg_entry.grid(row=1, column=1, sticky="ew", padx=5, ipady=10)
        bottom_frame.grid_columnconfigure(1, weight=1)
        self.msg_entry.focus()
        self.msg_entry.bind("<Return>", self._on_enter_pressed)

        # send button
        send_button = Button(bottom_frame, text="▶️", font="Helvetica 15", bg=BG, command=lambda: (self._on_enter_pressed(None), setattr(self, 'send_enabled', True)))
        send_button.grid(row=1, column=2, sticky="e", padx=5, ipady=10)

        # Second Frame on top of bottom frame
        bottom2_frame = Frame(self.window, bg=BG, height=80)
        bottom2_frame.pack(fill=X, side=BOTTOM, pady=0, padx=10)

        # Uploaded file label
        self.uploaded_file_label = Label(bottom2_frame, bg="#000000", fg=TEXT_COLOR, font=FONT, anchor="w")
        self.uploaded_file_label.pack(side="top", fill="x", expand=True)

    def _upload_file(self):
        filetypes = [("Word Documents", "*.docx"), ("PDF Files", "*.pdf")]
        filename = filedialog.askopenfilename(filetypes=filetypes, title="Select a File")
        if filename:
            # Copy the file to placeholder location
            file_basename = os.path.basename(filename)
            dest_path = os.path.join(os.getcwd(), file_basename)
            shutil.copy(filename, dest_path)

            # Store path and update file label and enable deletion
            self.uploaded_file_path = dest_path
            self.uploaded_file_label.config(text=f"{file_basename} [X]", fg="white", cursor="hand2")
            self.uploaded_file_label.bind("<Button-1>", self._remove_uploaded_file)

    def _remove_uploaded_file(self, event):
        if self.uploaded_file_path and os.path.exists(self.uploaded_file_path):
            os.remove(self.uploaded_file_path)
            self.uploaded_file_path = None
        self.uploaded_file_label.config(text="")
    
    

    def _on_enter_pressed(self, event):

        if not self.send_enabled:
            return
        
        if event and event.keysym == 'Return' and (event.state & 0x0001 or event.state & 0x0200):  # Check for Shift key being pressed
            self.msg_entry.insert(END, '\n')
        
        textboxtext = self.msg_entry.get("1.0", "end-1c")

        if not textboxtext.strip() and not self.uploaded_file_path:
            return
        
        else:
            mode = []
            cv_text = ""
            outputtext = textboxtext
            combined_text = textboxtext

            if self.uploaded_file_path:
                try:
                    converter = CvConverter(self.uploaded_file_path)
                    cv_text = converter.convert_to_text()
                    combined_text.append("\n" + cv_text)
                    outputtext = textboxtext + "\n+ (" + self.uploaded_file_path + ")"
                except Exception as e:
                    logging.warning(f"Error converting CV to text: {str(e)}")
                    return
            self._insert_message(outputtext, "You")

            if any(keyword in combined_text.lower() for keyword in CAREER_KEY):
                mode.append("career")
            elif any(keyword in combined_text.lower() for keyword in SKILL_KEY):
                mode.append("skill")
            else:
                # Default to career data if no match is found
                mode.append("career")

            # Preventing circular import
            from main import answer_question
            # Call the answer_question function with the correct arguments
            history, response = answer_question(
                textboxtext,
                cv_text,
                mode
            )

            self._insert_message(response, BOT_NAME)
            self.send_enabled = False  # Disable sending after message is sent
            return history

    def _insert_message(self, msg, sender):
        if not msg:
            return
        
        self.msg_entry.delete("1.0", END)
        output_msg = f"{sender}: {msg}\n"
        self.text_widget.configure(state=NORMAL)
        self.text_widget.insert(END, output_msg)
        self.text_widget.configure(state=DISABLED)

        def is_at_bottom():
            # Get the current position of the scrollbar (yview returns a tuple with min and max)
            _, end_pos = self.text_widget.yview()
            # If the max value is close to 1 (end), the user is at the bottom
            return end_pos >= 0.99
        if is_at_bottom():
            # Scroll to the end of the text widget
            self.text_widget.see(END)


if __name__ == "__main__":
    app = ChatGUI()
    app.run()
