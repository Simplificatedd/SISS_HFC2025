import React, { useState, useRef, useEffect } from "react";
import axios from "axios";
import "../styles/chatbot.css";
import { Button } from "@mui/material";
import ReactMarkdown from "react-markdown";

const Chatbot = () => {
  const [messages, setMessages] = useState([]);
  const [recommendations, setRecommendations] = useState([]);
  const [selectedDetail, setSelectedDetail] = useState(null);
  const [selectedOptions, setSelectedOptions] = useState([]); // To track detailed action buttons
  const [input, setInput] = useState("");
  const [file, setFile] = useState(null);
  const [mode, setMode] = useState("career");
  const [isTyping, setIsTyping] = useState(false);
  const fileInputRef = useRef(null);
  const messagesEndRef = useRef(null);

  // Auto-scroll to the latest message
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isTyping]);

  const handleSend = async () => {
    if (!input.trim() && !file) {
      setMessages([...messages, { sender: "Bot", text: "Please provide some input to proceed." }]);
      return;
    }
  
    setRecommendations([]); // Clear recommendations
    setSelectedDetail(null); // Clear selected detail
    setSelectedOptions([]); // Clear detailed action options
  
    const newMessages = [...messages, { sender: "You", text: input || "Uploaded resume." }];
    setMessages(newMessages);
  
    setInput("");
  
    const formData = new FormData();
    formData.append("message", input || ""); // Allow empty input if a file is uploaded
    formData.append("mode", mode);
    formData.append("history", JSON.stringify(messages));
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
        if (response.data.recommendations?.length > 0) {
          setMessages((prev) => [
            ...prev,
            {
              sender: "Bot",
              text: "Click on a recommendation below to learn more:",
              recommendations: response.data.recommendations,
            },
          ]);
        }
      } else {
        setMessages([...newMessages, { sender: "Bot", text: response.data.response }]);
      }
    } catch (error) {
      setIsTyping(false);
      setMessages([...newMessages, { sender: "Bot", text: "Unable to connect to the server." }]);
    }
  };
  
  const handleRecommendationClick = async (title) => {
    // Add the user message for their query
    const userQuery = `Could you share with me more about ${title}?`;
    setMessages((prev) => [
      ...prev,
      { sender: "You", text: userQuery },
    ]);
  
    try {
      const response = await axios.post("http://127.0.0.1:5000/api/details", { title, mode });
      const details = response.data.details;
  
      setSelectedDetail(details); // Store selected details
      setMessages((prev) => [
        ...prev,
        {
          sender: "Bot",
          text: `What would you like to know about **${title}** ${
          mode === "career" ? `by **${details.Company}**` : `from **${details.Institution}**`
          }?`,
          options: mode === "career"
            ? ["Company", "Location", "Employment Type", "Salary", "Job Description", "Go to Listing"]
            : [
                "Upcoming Date",
                "Duration",
                "Training Mode",
                "Full Fee",
                "Funded Fee",
                "About This Course",
                "What You'll Learn",
                "Minimum Entry Requirement",
                "Go to Listing",
              ],
        },
      ]);
    } catch (error) {
      setMessages((prev) => [
        ...prev,
        { sender: "Bot", text: "Unable to fetch details. Please try again later." },
      ]);
    }
  };
  
  const handleOptionClick = async (option) => {

     // Skip adding a user message for "Go to Listing"
    if (option === "Go to Listing") {
      window.open(selectedDetail.Link, "_blank");
      return;
    }
    // Display the user's choice as a message
    const userQuery = `Can you share with me more regarding ${option}?`;
    setMessages((prev) => [
      ...prev,
      { sender: "You", text: userQuery },
    ]);
  
    if (option === "Go to Listing") {
      window.open(selectedDetail.Link, "_blank");
    } else {
      const value = selectedDetail[option] || "N/A";
  
      if (value === "N/A" || value.trim() === "") {
        setMessages((prev) => [
          ...prev,
          { sender: "Bot", text: `Sorry, there is no information available for ${option}.` },
        ]);
        return;
      }
  
      try {
        setIsTyping(true); // Show typing indicator
        const response = await axios.post("http://127.0.0.1:5000/api/paraphrase", {
          text: `${option}: ${value}`,
        });
  
        setIsTyping(false);
  
        if (response.data.status === "success") {
          setMessages((prev) => [
            ...prev,
            { sender: "Bot", text: response.data.text },
          ]);
        } else {
          setMessages((prev) => [
            ...prev,
            { sender: "Bot", text: `Sorry, I couldn't summarize the information for ${option}.` },
          ]);
        }
      } catch (error) {
        setIsTyping(false);
        setMessages((prev) => [
          ...prev,
          { sender: "Bot", text: "An error occurred while summarizing the information. Please try again later." },
        ]);
      }
    }
  };
  
  const handleFileChange = (e) => {
    const selectedFile = e.target.files[0];

    if (selectedFile && selectedFile.type !== "application/pdf") {
      setMessages((prev) => [
        ...prev,
        { sender: "Bot", text: "Only PDF files are allowed. Please upload a valid file." },
      ]);
      fileInputRef.current.value = "";
      return;
    }

    setFile(selectedFile);
  };

  const handleFileRemove = () => {
    setFile(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
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
        <div
          key={index}
          className={`chatbot-message ${msg.sender === "You" ? "user-message" : "bot-message"}`}
        >
          {msg.sender === "Bot" ? (
            <ReactMarkdown>{msg.text}</ReactMarkdown>
          ) : (
            <div>{msg.text}</div>
          )}
          {msg.recommendations && (
            <div>
              {msg.recommendations.map((rec, idx) => (
                <Button
                  key={idx}
                  variant="outlined"
                  color="primary"
                  style={{ margin: "5px" }}
                  onClick={() => handleRecommendationClick(rec.title)}
                >
                  {rec.title}
                </Button>
              ))}
            </div>
          )}
          {msg.options && (
            <div>
              {msg.options.map((opt, idx) => (
                <Button
                  key={idx}
                  variant="outlined"
                  color="primary"
                  style={{ margin: "5px" }}
                  onClick={() => handleOptionClick(opt)}
                >
                  {opt}
                </Button>
              ))}
            </div>
          )}
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
      <div ref={messagesEndRef} />
    </div>


      <div className="chatbot-input-container">
        {file && (
          <div className="file-uploaded">
            {file.name}{" "}
            <button className="file-remove-button" onClick={handleFileRemove}>
              ✖
            </button>
          </div>
        )}
        <div className="chatbot-input-bar">
          <label className="chatbot-attach-button">
            +
            <input
              type="file"
              onChange={handleFileChange}
              className="chatbot-file-input"
              ref={fileInputRef}
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
