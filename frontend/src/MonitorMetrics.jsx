import {useParams} from "react-router-dom";
import {useEffect,useState} from 'react';
function MonitorMetrics(){
    const {monitor_id}=useParams();
    const BACKEND_URL=import.meta.env.VITE_BACKEND_URL;
    const [metrics,setMetrics]=useState([]);
    const [errorMessage,setErrorMessage]=useState("");
    async function handleGetMonitorMetrics(){
        setMetrics([]);
        try {
            const response=await fetch(`${BACKEND_URL}/monitors/${monitor_id}`,{
                "method":"GET",
                "headers":{
                    "Content-Type":"application/json"
                }
            });

            const result=await response.json()

            if (response.status!=200){
                setErrorMessage("Something went wrong");
            }
            else if (result.data.length===0){
                setErrorMessage(result.message);
            }
            else {
                setMetrics(result.data);
            }
        }
        catch(e){
            setErrorMessage(`Something went wrong: ${e}`)
        }
        finally{

        }


    }
    useEffect(()=>{
        handleGetMonitorMetrics()
    },[])
    return (
        <>
        {errorMessage && (
            <p className="mt-4 text-red-600">{errorMessage}</p>
        )}
        {metrics && Object.keys(metrics).length===3 && (
            <div>
            <p>Monitor metrics for {monitor_id}</p>
            <p>Uptime Percentage: {metrics["uptime_percentage"]}%</p>
            <p>Average Latency: {metrics["average_latency_ms"]} ms</p>
            <p>Error Rate: {metrics["error_rate"]}%</p>
            </div>
        )}
        

        </>
    )
}
export default MonitorMetrics
