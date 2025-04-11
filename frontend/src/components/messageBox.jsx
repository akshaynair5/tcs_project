import userImage from "../assets/user.png";
import assistantImage from "../assets/bot.png";

const MessageBox = ({ content, role }) => {
  // Normalize assistant role names
  const isUser = role === "user";
  const isAssistant = role === "assistant" || role === "ai_assistant" || role === "system";

  const profileImage = isUser ? userImage : assistantImage;

  // Handle content variations
  const messageText = content;

  return (
    <div className={`flex text-align-left gap-3 w-[75vw] ${isUser ? "flex-row-reverse items-end" : "items-start"} animate-fade-in`}>
      <img
        src={profileImage}
        alt="profile"
        className="w-8 h-8 rounded-full border-2 border-gray-400"
      />
      <div
        className={`p-3 max-w-xs md:max-w-md rounded-xl shadow-sm ${
          isUser ? "bg-blue-500 text-white" : "bg-gray-200 text-black"
        }`}
      >
        {messageText}
      </div>
    </div>
  );
};

export default MessageBox;
