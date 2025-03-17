import userImage from "../assets/user.png";
import assistantImage from "../assets/bot.png";

const MessageBox = ({ text, sender }) => {
  
    const profileImage = sender === "user" ? userImage : assistantImage;
  
    return (
      <div
        className={`flex items-start gap-3 ${
          sender === "user" ? "flex-row-reverse mr-10" : ""
        }`}
      >
        <img
          src={profileImage}
          alt="profile"
          className="w-8 h-8 rounded-full"
        />
        <div
          className={`p-3 max-w-xs md:max-w-md rounded-lg text-left ${
            sender === "user"
              ? "bg-blue-500 text-white"
              : "bg-gray-200 text-black"
          }`}
        >
          {text}
        </div>
      </div>
    );
  };
  
  export default MessageBox;
  