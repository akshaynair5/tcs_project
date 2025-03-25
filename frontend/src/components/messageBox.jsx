import userImage from "../assets/user.png";
import assistantImage from "../assets/bot.png";

const MessageBox = ({ content, role }) => {
  // Determine profile image
  const profileImage = role === "user" ? userImage : assistantImage;

  // Extract message content based on role
  const messageText =
    role === "assistant" && typeof content === "object"
      ? content.response_with_context || "No response available"
      : content;
  console.log(messageText)
  return (
    <div className={`flex gap-3 w-[75vw] ${role === "user" ? "flex-row-reverse items-end" : "items-start"}`}>
      <img src={profileImage} alt="profile" className="w-8 h-8 rounded-full" />
      <div
        className={`p-3 max-w-xs md:max-w-md rounded-lg text-left ${
          role === "user" ? "bg-blue-500 text-white" : "bg-gray-200 text-black"
        }`}
      >
        {messageText}
      </div>
    </div>
  );
};

export default MessageBox;
