import React, { useState, useRef, useEffect } from "react";
import axios from "axios";
import "../styles/chatbot.css";
import { Button, Typography } from "@mui/material";

const Chatbot = () => {
  const [messages, setMessages] = useState([]);
  const [recommendations, setRecommendations] = useState([]);
  const [selectedDetail, setSelectedDetail] = useState(null);
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
      setMessages([...messages, { sender: "Bot", text: "Please upload your resume before continuing." }]);
      return;
    }

    setRecommendations([]); // Clear recommendations
    setSelectedDetail(null); // Clear selected detail

    const newMessages = [...messages, { sender: "You", text: input || "Uploaded resume." }];
    setMessages(newMessages);

    setInput("");

    const formData = new FormData();
    formData.append("message", input);
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
        setRecommendations(response.data.recommendations || []);
        if (response.data.recommendations && response.data.recommendations.length > 0) {
          setMessages((prev) => [
            ...prev,
            { sender: "Bot", text: "Click on a recommendation below to learn more." },
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
    try {
      const response = await axios.post("http://127.0.0.1:5000/api/details", { title, mode });
      const details = response.data.details;

      // Initialize formatted details
      let formattedDetails = "";

      const appendField = (label, value) => {
        if (value && value !== "N/A") {
          formattedDetails += `<strong>${label}:</strong> ${value}<br />`;
        }
      };

      if (mode === "career") {
        appendField("Job Title", title);
        appendField("Company", details.Company);
        appendField("Employment Type", details["Employment Type"]);
        appendField("Location", details.Location);
        appendField("Salary", details.Salary);

        if (details["Job Description"]) {
          const description = details["Job Description"];
          const responsibilities = description.match(/Roles & Responsibilities(.*?)(Requirements|$)/s)?.[1]?.trim() || "";
          const requirements = description.match(/Requirements:(.*?)(Benefits|$)/s)?.[1]?.trim() || "";
          const benefits = description.match(/Benefits:(.*)/s)?.[1]?.trim() || "";

          if (responsibilities) {
            formattedDetails += `<strong>Key Responsibilities:</strong><br />${responsibilities
              .split("\n")
              .filter((line) => line.trim())
              .map((line) => `- ${line.trim()}`)
              .join("<br />")}<br /><br />`;
          }

          if (requirements) {
            formattedDetails += `<strong>Requirements:</strong><br />${requirements
              .split("\n")
              .filter((line) => line.trim())
              .map((line) => `- ${line.trim()}`)
              .join("<br />")}<br /><br />`;
          }

          if (benefits) {
            formattedDetails += `<strong>Benefits:</strong><br />${benefits
              .split("\n")
              .filter((line) => line.trim())
              .map((line) => `- ${line.trim()}`)
              .join("<br />")}`;
          }
        }
      } else if (mode === "skill") {
        appendField("Course Title", title);
        appendField("Institution", details.Institution);
        appendField("Upcoming Date", details["Upcoming Date"]);
        appendField("Duration", details.Duration);
        appendField("Training Mode", details["Training Mode"]);
        appendField("Full Fee", details["Full Fee"]);
        appendField("Funded Fee", details["Funded Fee"]);

        if (details["About This Course"] && details["About This Course"] !== "N/A") {
          formattedDetails += `<strong>About This Course:</strong><br />${details["About This Course"]
            .replace(/\n/g, "<br />")}<br /><br />`;
        }
        if (details["What You'll Learn"] && details["What You'll Learn"] !== "N/A") {
          formattedDetails += `<strong>What You'll Learn:</strong><br />${details["What You'll Learn"]
            .split("\n")
            .map((line) => `- ${line.trim()}`)
            .join("<br />")}<br /><br />`;
        }
        if (details["Minimum Entry Requirement"] && details["Minimum Entry Requirement"] !== "N/A") {
          formattedDetails += `<strong>Minimum Entry Requirement:</strong><br />${details["Minimum Entry Requirement"]
            .replace(/\n/g, "<br />")}<br />`;
        }
      }

      setSelectedDetail(details); // Store the selected detail
      setRecommendations([]); // Clear recommendations
      setMessages([
        ...messages,
        { sender: "Bot", text: formattedDetails },
      ]);
    } catch (error) {
      setMessages([...messages, { sender: "Bot", text: "Unable to fetch details." }]);
    }
  };

  const handleFileChange = (e) => {
    const selectedFile = e.target.files[0];

    if (selectedFile && selectedFile.type !== "application/pdf") {
      setMessages([...messages, { sender: "Bot", text: "Only PDF files are allowed. Please upload a valid file." }]);
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
              <div dangerouslySetInnerHTML={{ __html: msg.text }} />
            ) : (
              msg.text
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

      {/* Recommendations Section */}
      {recommendations.length > 0 && (
        <div className="chatbot-recommendations" style={{ textAlign: "center", margin: "10px 0" }}>
          {recommendations.map((rec, index) => (
            <Button
              key={index}
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

      {/* Selected Detail Section */}
      {selectedDetail && (
        <div style={{ textAlign: "center", margin: "10px 0" }}>
          <Button
            variant="outlined"
            color="primary"
            onClick={() => window.open(selectedDetail.Link, "_blank")}
          >
            View Full Details
          </Button>
        </div>
      )}

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
