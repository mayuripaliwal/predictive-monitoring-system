import CreateMonitorForm from './CreateMonitorForm';
import Navbar from './Navbar';
import {Routes, Route,Navigate} from "react-router-dom";
import Monitors from './Monitors';
import MonitorMetrics from './MonitorMetrics';
function App(){
  return (
    <>
    <Navbar/>
    <Routes>
      <Route path="/" element={<Navigate to='/monitors' replace/>}/>
      <Route path="/monitors" element={<Monitors/>}/>
      <Route path="/create-monitor" element={<CreateMonitorForm/>}/>
      <Route path="/monitors/:monitor_id" element={<MonitorMetrics/>}/>
    </Routes>
    </>
  )
}

export default App