import { useContext, useState } from "react";
import { AuthContext } from "../contextProvider";
import axios from "axios";

const ChatSidebar = () => {
    const { currentUserData, currentChat, setCurrentChat, currentUser } = useContext(AuthContext);
    const [newChatTitle, setNewChatTitle] = useState("");

    // Function to create a new chat
    const createChat = async () => {
        if (!newChatTitle.trim()) return;

        try {
            const response = await axios.post("http://127.0.0.1:5000/api/chat", {
                user_id: currentUser.user_id,
                title: newChatTitle,
            });

            if (response.status === 201) {
                // Add the new chat to the list
                setCurrentChat({
                    _id: response.data.chat_id,
                    title: newChatTitle,
                    lastMessage: "",
                    lastMessageTime: "Just now",
                });

                // Clear input field
                setNewChatTitle("");
            }
        } catch (error) {
            console.error("Failed to create chat", error);
        }
    };

    return (
        <aside className="w-[20vw] h-screen bg-gray-900 text-white p-4 overflow-y-auto z-10 flex flex-col">
            <h2 className="text-xl font-bold mb-4">Chats</h2>

            {/* New Chat Input */}
            <div className="mb-4 flex">
                <input
                    type="text"
                    placeholder="Chat title..."
                    value={newChatTitle}
                    onChange={(e) => setNewChatTitle(e.target.value)}
                    className="flex-grow p-2 rounded-l bg-gray-800 text-white border border-gray-700 focus:outline-none"
                />
                <button
                    onClick={createChat}
                    className="bg-blue-600 p-2 rounded-r hover:bg-blue-700"
                >
                    +
                </button>
            </div>

            {/* Chat List */}
            <ul className="flex-grow overflow-auto">
                {currentUserData?.chats?.length > 0 ? (
                    currentUserData.chats.map((chat) => (
                        <li
                            key={chat._id}
                            className={`p-3 mb-2 rounded-lg cursor-pointer 
                                ${currentChat?._id === chat._id ? "bg-blue-600" : "bg-gray-800"}`}
                            onClick={() => setCurrentChat(chat)}
                        >
                            <div className="flex justify-between items-center">
                                <span className="font-semibold">{chat.title}</span>
                                <span className="text-sm text-gray-400">
                                    {chat.lastMessageTime
                                        ? new Date(chat.lastMessageTime).toLocaleString("en-US", {
                                            weekday: "short", // "Wed"
                                            hour: "2-digit",  // "00"
                                            minute: "2-digit" // "23"
                                        })
                                        : "No messages"}
                                </span>
                            </div>
                            <p className="text-gray-300 text-sm truncate">{chat.lastMessage.response_with_context? chat.lastMessage.response_with_context : chat.lastMessage || "Start chatting..."}</p>
                        </li>
                    ))
                ) : (
                    <p className="text-gray-400">No chats available</p>
                )}
            </ul>
        </aside>
    );
};

export default ChatSidebar;
