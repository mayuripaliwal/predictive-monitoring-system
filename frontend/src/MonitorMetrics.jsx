import {useParams} from "react-router-dom";
import {useEffect,useState} from 'react';
import {formatDateTime} from './Monitors';

const ERROR_THRESHOLD=1;
function MonitorMetrics(){
    const {monitor_id}=useParams();
    const BACKEND_URL=import.meta.env.VITE_BACKEND_URL;
    
    const [metricsErrorMessage,setMetricsErrorMessage]=useState("");

    const [metrics,setMetrics]=useState([]);
    const [loadingMetrics,setLoadingMetrics]=useState(false);

    const [monitorEventsErrorMessage, setMonitorEventsErrorMessage]=useState("");

    const [monitor_events,setMonitorEvents]=useState([]);
    const [loadingMonitorEvents,setLoadingMonitorEvents]=useState(false);

    async function handleGetMonitorMetrics(){
        setLoadingMetrics(true);
        setMetricsErrorMessage("");
        setMetrics([]);
        try {
            const response=await fetch(`${BACKEND_URL}/monitors/${monitor_id}/metrics`,{
                "method":"GET",
                "headers":{
                    "Content-Type":"application/json"
                }
            });

            const result=await response.json()

            if (response.status!=200){
                setMetricsErrorMessage("Something went wrong. Please try again later.");
            }
            else if (result.data.length===0){
                setMetricsErrorMessage(result.message);
            }
            else {
                setMetrics(result.data);
            }
        }
        catch(e){
            setMetricsErrorMessage("Unable to connect to the server. Please try again later.");
        }
        finally{
            setLoadingMetrics(false);
        }


    }
    async function handleGetMonitorEvents(){
        setMonitorEventsErrorMessage("");
        setLoadingMonitorEvents(true);
        setMonitorEvents([]);
        try{
            const response=await fetch(`${BACKEND_URL}/monitors/${monitor_id}/events`);

            const result=await response.json()

            if (response.status!=200){
                setMonitorEventsErrorMessage("Something went wrong. Please try again later.");
            }
            else if (result.data.length===0){
                setMonitorEventsErrorMessage(result.message);
            }
            else {
                setMonitorEvents(result.data);
            }
            
        }
        catch(e){
            setMonitorEventsErrorMessage("Unable to connect to the server. Please try again later.");
        }
        finally{
            setLoadingMonitorEvents(false);
        }
    }
    useEffect(()=>{
        handleGetMonitorMetrics(), 
        handleGetMonitorEvents()
    },[])
    return (
        <>
        {metricsErrorMessage && (
            <p className="mt-4 text-red-600 text-lg">{metricsErrorMessage}</p>
        )}
        {/*Loading Metrics */}
        {loadingMetrics && (
            <p className="mt-4 text-gray-900 text-lg">Loading metrics...</p>
        )}
        {/*Metrics Card */}
        {metrics && Object.keys(metrics).length===5 && 
            (
                <div className="mt-4 mx-auto max-w-10/12">
                    <h3 className="text-left text-2xl font-semibold text-gray-900">{metrics["monitor_name"]}</h3>
                    <h3 className="text-left text-base font-semibold text-gray-900">
                        <a href={metrics["monitor_url"]} target="_blank" rel="noreferrer">
                            {metrics["monitor_url"]}
                        </a>
                    </h3>
                    <dl className="mt-5 grid grid-cols-1 gap-5 sm:grid-cols-3">
                        <div className="overflow-hidden rounded-lg bg-white px-4 py-5 shadow-sm sm:p-6">
                            <dt className="truncate text-sm font-medium text-gray-500">Uptime Percentage</dt>
                            <dd className="mt-1 text-3xl font-semibold tracking-tight text-emerald-600">{metrics["uptime_percentage"].toFixed(2)}%</dd>
                        </div>
                        <div className="overflow-hidden rounded-lg bg-white px-4 py-5 shadow-sm sm:p-6">
                            <dt className="truncate text-sm font-medium text-gray-500">Average Latency</dt>
                            <dd className="mt-1 text-3xl font-semibold tracking-tight text-gray-900">{metrics["average_latency_ms"]?metrics["average_latency_ms"].toFixed(2):"N/A"}
                                {metrics["average_latency_ms"] && (<span className="text-sm text-gray-500"> ms</span>)}
                            </dd>
                        </div>
                        <div className="overflow-hidden rounded-lg bg-white px-4 py-5 shadow-sm sm:p-6">
                            <dt className="truncate text-sm font-medium text-gray-500">Error Rate</dt>
                            <dd className={`mt-1 text-3xl font-semibold tracking-tight ${metrics["error_rate"]>ERROR_THRESHOLD?"text-red-600":"text-emerald-600"}`}>{metrics["error_rate"].toFixed(2)}%</dd>
                        </div>
                    </dl>
                    <p className="text-right mt-2 text-sm text-gray-500">Based on past 24 hours data</p>
                </div>
            )
        }
        {/*Error Message: Recent monitor events */}
        {monitorEventsErrorMessage && (
            <p className="mt-4 text-red-600 text-lg">{monitorEventsErrorMessage}</p>
        )}
        {/*10 Recent monitor events */}
        {monitor_events.length>0 && (
            <div className="mx-auto max-w-10/12 py-6">
                <div className="sm:flex sm:items-center">
                    <div className="sm:flex-auto">
                    <h1 className="text-left text-xl font-semibold text-gray-900">Recent Checks</h1>
                    </div>
                </div>
                <div className="mt-8 flow-root">
                    <div className="-mx-4 -my-2 overflow-x-auto sm:-mx-6 lg:-mx-8">
                    <div className="inline-block min-w-full py-2 align-middle sm:px-6 lg:px-8">
                        <div className="overflow-hidden shadow-sm outline-1 outline-black/5 sm:rounded-lg">
                        <table className="relative min-w-full divide-y divide-gray-300">
                            <thead className="bg-gray-50">
                            <tr>
                                <th scope="col" className="py-3.5 pr-3 pl-4 text-center text-sm font-semibold text-gray-900 sm:pl-6">
                                Time
                                </th>
                                <th scope="col" className="px-3 py-3.5 text-center text-sm font-semibold text-gray-900">
                                Status
                                </th>
                                <th scope="col" className="px-3 py-3.5 text-center text-sm font-semibold text-gray-900">
                                Latency (ms)
                                </th>
                                <th scope="col" className="px-3 py-3.5 text-center text-sm font-semibold text-gray-900">
                                Status Code
                                </th>
                            </tr>
                            </thead>
                            <tbody className="divide-y divide-gray-200 bg-white">
                            {monitor_events.map((monitor_event) => (
                                <tr key={monitor_event.id}>
                                <td className="px-3 py-4 text-sm whitespace-nowrap text-gray-600">
                                    {formatDateTime(monitor_event.checked_at)}
                                </td>
                                <td className="px-3 py-4 text-sm whitespace-nowrap text-gray-600">{monitor_event.status}</td>
                                <td className="px-3 py-4 text-sm whitespace-nowrap text-gray-600">{monitor_event.response_time_ms}</td>
                                <td className="px-3 py-4 text-sm whitespace-nowrap text-gray-600">{monitor_event.status_code}</td>
                                </tr>
                            ))}
                            </tbody>
                        </table>
                        </div>
                    </div>
                    </div>
                </div>
            </div>
        )}
        </>
    )
}
export default MonitorMetrics
