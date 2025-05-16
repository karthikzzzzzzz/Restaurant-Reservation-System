import ChatBotIcon from "./ChatBotIcon";
import { AiOutlineUser } from "react-icons/ai";

const ChatMessage = ({ chat }) => {
    return (
        <div className={`message ${chat.role === "chatbot" ? 'bot' : 'user'}-message`}>
            {chat.role === 'chatbot' ? <ChatBotIcon /> : <AiOutlineUser />}
            <p className="message-text">{chat.text}</p>
        </div>
    );
};

export default ChatMessage;
