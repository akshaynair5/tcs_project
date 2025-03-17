import ChatInput from "../components/chatBar";
import ChatComponent from "../components/chatComponent";

function Home(){
    return(
        <div className='bg-slate-700 fixed top-0 left-0 h-screen w-screen'>
            <ChatComponent></ChatComponent>
        </div>
    )
}

export default Home;