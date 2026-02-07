import React from "react";
import Section from "./Section";

const NetworkSection = ({ products }) => {
  
  const labelKeyMap = {
    "Sim Size": "sim",
    "Network Support": "wireless_tech",
    "Wi-Fi": "connectivity",
    "Wi-Fi Features": "wifi_features", 
    Bluetooth: "bluetooth",            
  };

  const networkLabels = Object.keys(labelKeyMap);

  return (
    <Section
      title="Network & Connectivity"
      labels={networkLabels}
      products={products}
      sectionKey="network&connectivity"
      labelKeyMap={labelKeyMap} 
    />
  );
};

export default NetworkSection;
