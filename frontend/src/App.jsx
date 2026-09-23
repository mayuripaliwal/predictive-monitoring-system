import CreateMonitorForm from './CreateMonitorForm';
import Navbar from './Navbar';
import {Routes, Route,Navigate} from "react-router-dom";
import Monitors from './Monitors';
function App(){
  return (
    <>
    <Navbar/>
    <Routes>
      <Route path="/" element={<Navigate to='/monitors' replace/>}/>
      <Route path="/monitors" element={<Monitors/>}/>
      <Route path="/create-monitor" element={<CreateMonitorForm/>}/>
    </Routes>
    </>
  )
}

export default App