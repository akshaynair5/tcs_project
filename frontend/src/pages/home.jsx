import Sidebar from "../components/sidebar";
import ChatComponent from "../components/chatComponent";
import Navbar from "../components/navbar";

function Home(){
    return(
        <div className='bg-slate-700 fixed top-[10vh] left-0 h-[90vh] w-screen'>
            <Navbar></Navbar>
            <Sidebar></Sidebar>
            <ChatComponent></ChatComponent>
        </div>
    )
}

export default Home;