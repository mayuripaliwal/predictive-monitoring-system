import {useEffect} from 'react';
import {useState} from 'react';
const BACKEND_URL=import.meta.env.VITE_BACKEND_URL;
function MonitorsTable({monitors}) {
    return (
    <div className="px-4 sm:px-6 lg:px-8">
      <div className="mt-8 flow-root">
        <div className="-mx-4 -my-2 overflow-x-auto sm:-mx-6 lg:-mx-8">
          <div className="mx-auto w-full py-2 align-center sm:px-6 lg:px-8">
            <table className="w-full divide-y divide-gray-300">
              <thead>
                <tr>
                  <th scope="col" className="py-3.5 pr-3 pl-4 text-center text-sm font-semibold text-gray-900 sm:pl-3">
                    Name
                  </th>
                  <th scope="col" className="px-3 py-3.5 text-center text-sm font-semibold text-gray-900">
                    URL
                  </th>
                  <th scope="col" className="px-3 py-3.5 text-center text-sm font-semibold text-gray-900">
                    Status
                  </th>
                  <th scope="col" className="px-3 py-3.5 text-center text-sm font-semibold text-gray-900">
                    Status Code
                  </th>
                  <th scope="col" className="px-3 py-3.5 text-center text-sm font-semibold text-gray-900">
                    Response Time (ms)
                  </th>
                  <th scope="col" className="px-3 py-3.5 text-center text-sm font-semibold text-gray-900">
                    Last Checked
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white">
                {monitors.map((monitor) => (
                  <tr key={monitor.url} className="even:bg-gray-50">
                    <td className="text-center py-4 pr-3 pl-4 text-sm font-medium whitespace-nowrap text-gray-900 sm:pl-3">
                      {monitor.name}
                    </td>
                    <td className="text-center px-3 py-4 text-sm whitespace-nowrap text-gray-500">{monitor.url}</td>
                    <td className="text-center px-3 py-4 text-sm whitespace-nowrap text-gray-500">{monitor.status==null?"Pending":monitor.status=="up"?"Up":"Down"}</td>
                    <td className="text-center px-3 py-4 text-sm whitespace-nowrap text-gray-500">{monitor.status_code==null?"None":monitor.status_code}</td>
                    <td className="text-center px-3 py-4 text-sm whitespace-nowrap text-gray-500">{monitor.response_time_ms==null?"None":monitor.response_time_ms}</td>
                    <td className="text-center px-3 py-4 text-sm whitespace-nowrap text-gray-500">{formatDateTime(monitor.checked_at)}</td>
                    
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  )
}
//this function converts the timestamp into a user -friendly format
function formatDateTime(timestamp){
    //handle null timestamps (when monitor has not been checked yet)
    if (timestamp === null){
        return "None";
    }
    const options={
        day:"numeric",
        month:"short",
        year:"numeric",
        hour:"numeric",
        minute:"2-digit",
        hour12:true
    }
    const date=new Date(timestamp);
    return new Intl.DateTimeFormat(undefined,options).format(date);
}

export default function Monitors(){
    const [monitors,setMonitors]=useState([]);
    const [errorMessage, setErrorMessage]=useState("");
    const [loading,setLoading]=useState(false);
    {/* TODO: implement polling/sse for real-time monitor updates */}
    async function handleGetMonitors(){
        setLoading(true);
        setErrorMessage("");
        try{
            const response=await fetch(`${BACKEND_URL}/monitors`,{
                "method":"GET",
                headers:{
                    "Content-Type":"application/json"
                }
            });
            const result=await response.json();
            if (response.status===200){
                setMonitors(result);
                
            }
            else{
                setErrorMessage("Something went wrong. Please try again.");

            }
        }
        catch(e){
            setErrorMessage("Unable to connect to the server. Please try again.");
        }
        finally{
            setLoading(false);
        }
    }
    useEffect(()=>{
        handleGetMonitors();
    },[]);
    return (
        <>
        {loading && (
            <p className="text-gray-900">Loading monitors...</p>
        )}
        {errorMessage && (
            <p className="text-red-600">{errorMessage}</p>
        )}
        {monitors.length>0 && 
            (
                <MonitorsTable monitors={monitors}/>
            )
        }
        </>
    )
}