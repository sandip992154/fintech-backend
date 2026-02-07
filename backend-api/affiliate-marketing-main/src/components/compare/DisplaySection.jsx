import React from "react";
import Section from "./Section";

const DisplaySection = ({ products }) => {
  // Labels inside features.details.display
  const displayLabels = [
    "resolution",
    "touchscreen",
    "display_features", // rename "Display Type" or "Pixel Density" if needed
    "screen_size",
    "pixel_density",
  ];

  return (
    <Section
      title="Display"
      labels={displayLabels}
      products={products}
      sectionKey="display"
    />
  );
};

export default DisplaySection;
