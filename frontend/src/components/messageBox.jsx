import React, { useState } from 'react';
import userImage from "../assets/user.png";
import assistantImage from "../assets/bot.png";
import ReactMarkdown from 'react-markdown';

const MessageBox = ({ content, role }) => {
  const isUser = role === "user";
  const isAssistant = role === "assistant" || role === "ai_assistant" || role === "system";

  const profileImage = isUser ? userImage : assistantImage;

  // Determine if content is an object with togglable responses
  const isToggleContent = isAssistant && typeof content === "object" && content.response_short && content.response_detailed;

  const [showDetailed, setShowDetailed] = useState(false);

  // Resolve what message to show
  const messageText = isToggleContent
    ? (showDetailed ? content.response_detailed : content.response_short)
    : content;

  return (
    <div className={`flex text-left gap-3 w-[75vw] ${isUser ? "flex-row-reverse items-end" : "items-start"} animate-fade-in`}>
      <img
        src={profileImage}
        alt="profile"
        className="w-8 h-8 rounded-full border-2 border-gray-400"
      />
      <div className="flex flex-col gap-2">
        <div
          className={`p-3 max-w-xs md:max-w-md rounded-xl shadow-sm text-left ${
            isUser ? "bg-blue-500 text-white" : "bg-gray-200 text-black"
          }`}
        >
          <ReactMarkdown>{messageText}</ReactMarkdown>
        </div>
        {isToggleContent && (
          <button
            onClick={() => setShowDetailed(!showDetailed)}
            className="text-xs text-blue-500 hover:underline ml-2"
          >
            {showDetailed ? "Show Less" : "Show More"}
          </button>
        )}
      </div>
    </div>
  );
};

export default MessageBox;
