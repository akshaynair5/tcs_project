import { Link } from "react-router-dom";
import { useContext } from "react";
import { AuthContext } from "../contextProvider";
import logout from "./logout";
const Navbar = () => {
  
  return (
    <nav className="fixed top-0 left-0 w-full h-[10vh] bg-black text-white flex items-center px-6 shadow-md">
      <div className="container mx-auto flex justify-between items-center">
        <Link className="text-xl font-bold" to="/">Home</Link>
        <div>
          <ul className="flex space-x-6">
            <li>
              <button className="hover:text-gray-400 transition" onClick = {logout}>
                logout
              </button>
            </li>
          </ul>
        </div>
      </div>
    </nav>
  );
}

export default Navbar;
