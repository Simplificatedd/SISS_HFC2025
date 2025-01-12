from tkinter import *
from tkinter import filedialog
import shutil
import os
from CV_parser import CvConverter
from markdown_format import SimpleMarkdownText
import logging

BG = "#84848a"
BG_COLOR = "#020229"
TEXT_COLOR = "#ffffff"

FONT = "Helvetica 12"
FONT_BOLD = "Helvetica 12 bold"

BOT_NAME = "Debbie"
MODEL = "qwen2.5:3b"

CAREER_KEY = "career", "job", "position", "role", "careers", "jobs", "positions", "roles", "work", "employment", "occupation"
SKILL_KEY = "skill", "expertise", "technology", "competency", "skills", "expertises", "technologies", "competencies", "course", "courses"

class ChatGUI:
    def __init__(self):
        self.window = Tk()
        self.uploaded_file_label = None
        self.uploaded_file_path = None
        self._setup_main_window()
        self.send_enabled = False

    def run(self):
        self._insert_message("Would you like me to recommend Careers, or Courses for you?", BOT_NAME)
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
        self.text_widget = SimpleMarkdownText(self.window, bg=BG_COLOR, fg=TEXT_COLOR, font=FONT, padx=5, pady=5)
        self.text_widget.pack(expand=True, fill=BOTH, padx=10, pady=(10, 0))
        self.text_widget.configure(cursor="arrow", state="disabled")


        # Scrollbar
        # scrollbar = Scrollbar(self.text_widget)
        # scrollbar.pack(side=RIGHT, fill=Y)
        # scrollbar.configure(command=self.text_widget.yview)

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
        self.filename = filedialog.askopenfilename(filetypes=filetypes, title="Select a File")
        if self.filename:
            # Copy the file to placeholder location
            file_basename = os.path.basename(self.filename)
            dest_path = os.path.join(os.getcwd(), file_basename)
            shutil.copy(self.filename, dest_path)

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
            self.send_enabled = True
        
        
        textboxtext = self.msg_entry.get("1.0", "end-1c")

        if not textboxtext.strip() and not self.uploaded_file_path:
            return
        
        # Initialize text variables
        outputtext = textboxtext
        combined_text = textboxtext
        cv_text = ""
        cv_markdown = ""

        if not hasattr(self, 'mode') or not self.mode:
            self._insert_message(textboxtext, "You")

            if any(keyword in combined_text.lower() for keyword in CAREER_KEY):
                self.mode = ("career")
                output = "careers"
            elif any(keyword in combined_text.lower() for keyword in SKILL_KEY):
                self.mode = ("skill")
                output = "courses"
            else:
                self._insert_message(
                    "Sorry, I didn't understand that. Please type 'Careers' or 'Courses'.", BOT_NAME
                )
                return
            self._insert_message(f"Got it! I will suggest {output} suitable for you.", BOT_NAME)
            self._insert_message(
                "Please describe your skillset, industry preferences, or upload your CV for better assistance.",
                BOT_NAME
            )
            return
        
        
        if self.uploaded_file_path:
            try:
                converter = CvConverter(self.uploaded_file_path)
                cv_text = converter.convert_to_text()
                cv_markdown = CvConverter.export_to_markdown(self,cv_text)
                combined_text += "\n" + cv_markdown
                outputtext = textboxtext + "\n+ (" + self.filename + ")"
            except Exception as e:
                logging.warning(f"Error converting CV to text: {str(e)}")
                return
        self._insert_message(outputtext, "You")
        # Preventing circular import
        from main import answer_question
        # Call the answer_question function with the correct arguments
        history, response = answer_question(
            textboxtext,
            cv_markdown,
            [self.mode]
        )
        self.mode = None
        self._insert_message(response, BOT_NAME)
        self._insert_message("\n")
        self._insert_message("Now, would you like me to recommend Careers, or Courses for you?", BOT_NAME)
        self.msg_entry.delete("1.0", END)
        self.msg_entry.update_idletasks()
        self.msg_entry.focus()
        self.send_enabled = False  # Disable sending after message is sent
        return history

    def _insert_message(self, msg, sender = ""):
        if not msg:
            return
        
        if not sender:
            output_msg = f"{msg}\n"
            self.text_widget.configure(state=NORMAL)
            self.text_widget.insert(END, output_msg)
            self.text_widget.configure(state=DISABLED)
            self.msg_entry.delete("1.0", END)
            self.text_widget.see(END)  # Automatically scroll to the latest message
        else:
            output_msg = f"{sender}: {msg}\n"
            self.text_widget.configure(state=NORMAL)
            self.text_widget.insert(END, output_msg)
            self.text_widget.configure(state=DISABLED)
            self.msg_entry.delete("1.0", END)
            self.text_widget.see(END)  # Automatically scroll to the latest message
        
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
