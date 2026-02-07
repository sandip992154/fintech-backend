// import React from "react";
// import Section from "./Section";

// const DesignSection = ({ products }) => {
//   // Labels we want to show in the design section
//   const designSpecs = ["Width", "Thickness", "Weight"];

//   // Create data for Section: each product should have corresponding values
//   const productData = products.map((product) => ({
//     name: product.name,
//     specs: {
//       Width: product.width || "-",        // fallback if API value missing
//       Thickness: product.thickness || "-",
//       Weight: product.weight || "-",
//     },
//   }));

//   return (
//     <Section title="Design" labels={designSpecs} productData={productData} />
//   );
// };

// export default DesignSection;
import React from "react";
import Section from "./Section";

const DesignSection = ({ products }) => {
  const designLabels = ["dimensions", "weight", "form_factor", "color"];
  return (
    <Section
      title="Design"
      labels={designLabels}
      products={products}
      sectionKey="design"
    />
  );
};

export default DesignSection;
