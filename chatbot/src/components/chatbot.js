import React, { useState, useRef } from "react";
import axios from "axios";
import "../styles/chatbot.css";

const Chatbot = () => {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [file, setFile] = useState(null);
  const [mode, setMode] = useState("career");
  const [isTyping, setIsTyping] = useState(false);
  const fileInputRef = useRef(null); // Reference to the file input element

  const handleSend = async () => {
    if (!input.trim() && !file) return;

    const newMessages = [...messages, { sender: "You", text: input || "Uploaded resume." }];
    setMessages(newMessages);

    setInput("");

    const formData = new FormData();
    formData.append("message", input);
    formData.append("mode", mode);
    formData.append("history", JSON.stringify(messages)); // Send conversation history
    if (file) {
      formData.append("uploadedFile", file);
    }

    setIsTyping(true);
    try {
      const response = await axios.post("http://127.0.0.1:5000/api/chat", formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });

      setIsTyping(false);
      if (response.data.status === "success") {
        setMessages([...newMessages, { sender: "Bot", text: response.data.response }]);
      } else {
        setMessages([...newMessages, { sender: "Bot", text: response.data.response }]);
      }
    } catch (error) {
      setIsTyping(false);
      setMessages([...newMessages, { sender: "Bot", text: "Unable to connect to the server." }]);
    }
  };

  const handleFileChange = (e) => {
    const selectedFile = e.target.files[0];
    if (selectedFile) {
      setFile(selectedFile);
    }
  };

  const handleFileRemove = () => {
    setFile(null); // Clear the file state
    if (fileInputRef.current) {
      fileInputRef.current.value = ""; // Reset the file input element
    }
  };

  const toggleMode = () => {
    setMode((prevMode) => (prevMode === "career" ? "skill" : "career"));
  };

  return (
    <div className="chatbot-ui">
      <header className="chatbot-header">
        <div className="chatbot-header-left">
          <div className="chatbot-logo">JB</div>
          <h1 className="chatbot-title">Jobot</h1>
        </div>
        <div className="mode-selector-header">
          <span>{mode === "career" ? "Career" : "Skill"}</span>
          <label className="switch">
            <input type="checkbox" onChange={toggleMode} />
            <span className="slider"></span>
          </label>
        </div>
      </header>
      <div className="chatbot-messages">
        {messages.map((msg, index) => (
          <div key={index} className={`chatbot-message ${msg.sender === "You" ? "user-message" : "bot-message"}`}>
            {msg.text}
          </div>
        ))}
        {isTyping && (
          <div className="chatbot-message bot-message">
            <div className="typing-indicator">
              <span>.</span>
              <span>.</span>
              <span>.</span>
            </div>
          </div>
        )}
      </div>
      <div className="chatbot-input-container">
        {/* File Upload Section */}
        {file && (
          <div className="file-uploaded">
            {file.name}{" "}
            <button className="file-remove-button" onClick={handleFileRemove}>
              ✖
            </button>
          </div>
        )}

        {/* Input Bar */}
        <div className="chatbot-input-bar">
          <label className="chatbot-attach-button">
            +
            <input
              type="file"
              onChange={handleFileChange}
              className="chatbot-file-input"
              ref={fileInputRef} // Reference to the file input
            />
          </label>
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask anything."
            className="chatbot-input"
          />
          <button onClick={handleSend} className="chatbot-send-button">
            ➤
          </button>
        </div>
      </div>
    </div>
  );
};

export default Chatbot;
