import React from "react";
import "./HubTable.css";
const HubTable = ({ hubs }) => (
  <div className="hub-table-container"><table className="hub-table"><thead><tr><th>HUB</th><th>STABILITY</th><th>EFFICIENCY</th><th>BALANCE</th><th>ROLE</th><th>VOLUME %</th></tr></thead><tbody>{hubs && hubs.map((h,i)=>(<tr key={i}><td className="hub-name">{h.name}</td><td>{h.stability}</td><td>{h.efficiency}</td><td>{h.balance}</td><td><span className={`hub-role ${h.role==="Primary Hub"?"role-primary":"role-secondary"}`}>{h.role}</span></td><td>{h.volume}%</td></tr>))}</tbody></table></div>
);
export default HubTable;