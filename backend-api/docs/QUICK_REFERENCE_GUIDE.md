# Commission Management - Quick Reference Guide

**Date**: October 3, 2025  
**Quick Reference for Developers**

---

## 🚀 Quick Start

### **View Commission Modal Implementation**

```javascript
// 1. Add loading state to modal function
const openViewCommissionModal = useCallback(
  async (scheme) => {
    try {
      setIsModal((prev) => ({ ...prev, ViewCommision: true }));
      setOperationLoading("commission", true);

      const commissionData =
        await schemeManagementService.getAllCommissionsByScheme(scheme.id);
      setSelectedCommission(commissionData);
    } catch (error) {
      console.error("Error:", error);
      setSelectedCommission({});
    } finally {
      setOperationLoading("commission", false);
    }
  },
  [setOperationLoading]
);

// 2. Pass loading state to component
<CommissionTable
  data={selectedCommission}
  isLoading={isOperationLoading("commission")}
/>;
```

---

## 📋 API Reference

### **Commission Endpoints**

```bash
# Get commissions for specific service
GET /api/v1/schemes/{scheme_id}/commissions?service=mobile_recharge

# Available services
mobile_recharge | dth_recharge | bill_payments | aeps | dmt | micro_atm
```

### **Response Structure**

```json
{
  "service": "mobile_recharge",
  "entries": [
    {
      "id": 1,
      "operator": { "name": "Airtel" },
      "commission_type": "percentage",
      "admin": 4.0,
      "whitelabel": 3.0,
      "masterdistributor": 2.5,
      "distributor": 2.0,
      "retailer": 1.5
    }
  ]
}
```

---

## 🎯 Key Components

### **CommissionTable Props**

```javascript
<CommissionTable
  data={object}           // Required: Commission data by service
  isLoading={boolean}     // Optional: Loading state
  title={string}          // Optional: Modal title
  onSubmit={function}     // Optional: Submit callback
/>
```

### **Data Structure Expected**

```javascript
// Correct format for CommissionTable
{
  "Mobile Recharge": [
    { operator: {name: "Airtel"}, commission_type: "percentage", ... }
  ],
  "DTH Recharge": [...],
  "Bill Payments": [...],
  // ...
}
```

---

## 🔧 Service Methods

### **schemeManagementService.js**

```javascript
// Get commissions for all services
await getAllCommissionsByScheme(schemeId);
// Returns: { "Mobile Recharge": [...], "DTH Recharge": [...] }

// Get available service types
getServiceTypes();
// Returns: [{ value: "mobile_recharge", label: "Mobile Recharge" }, ...]
```

---

## 🐛 Common Issues

### **Issue: "map is not a function"**

```javascript
// ❌ Wrong: Passing scheme object directly
openViewCommissionModal(schemeObject);

// ✅ Correct: Fetch commission data first
const commissionData = await getAllCommissionsByScheme(scheme.id);
setSelectedCommission(commissionData);
```

### **Issue: "service field required"**

```javascript
// ❌ Wrong: Missing service parameter
GET /schemes/1/commissions

// ✅ Correct: Include service parameter
GET /schemes/1/commissions?service=mobile_recharge
```

### **Issue: Loading state not working**

```javascript
// ❌ Wrong: No loading state management
const openModal = () => {
  fetchCommissionData();
};

// ✅ Correct: Proper loading lifecycle
const openModal = async () => {
  setLoading(true);
  try {
    await fetchCommissionData();
  } finally {
    setLoading(false);
  }
};
```

---

## 🎨 UI Components

### **Loading Spinner**

```jsx
{
  isLoading ? (
    <div className="flex justify-center items-center h-40">
      <div className="animate-spin rounded-full h-12 w-12 border-4 border-gray-300 border-t-[#7C5CFC]"></div>
      <p>Loading commission data...</p>
    </div>
  ) : (
    <TableContent />
  );
}
```

### **Service Tabs**

```jsx
{
  services.map((service) => (
    <button
      key={service}
      onClick={() => setSelectedService(service)}
      className={selectedService === service ? "active" : "inactive"}
    >
      {service}
    </button>
  ));
}
```

### **Empty State**

```jsx
{
  (!data[selectedService] || data[selectedService].length === 0) && (
    <tr>
      <td colSpan="7" className="text-center text-gray-500 italic">
        No entries for "{selectedService}"
      </td>
    </tr>
  );
}
```

---

## 📊 Testing

### **Manual Test Steps**

1. Click "View Commission" on any scheme
2. ✅ Modal opens immediately
3. ✅ Loading spinner appears
4. ✅ Service tabs load (6 tabs)
5. ✅ Click different tabs to switch services
6. ✅ Table shows commission data or "No entries"

### **Console Debug**

```javascript
// Check data structure
console.log("Commission data:", selectedCommission);

// Check loading state
console.log("Is loading:", isOperationLoading("commission"));

// Check service types
console.log("Services:", Object.keys(commissionData));
```

---

## 🔍 Troubleshooting

### **No Service Tabs Showing**

- Check if `getAllCommissionsByScheme()` is being called
- Verify API endpoints are accessible
- Check browser network tab for 404/500 errors

### **Table Shows "N/A" Values**

- Verify commission data exists for the scheme
- Check field mapping: `operator.name`, `commission_type`, etc.
- Ensure backend returns correct field names

### **Loading Spinner Stuck**

- Check if `setOperationLoading("commission", false)` is called in `finally` block
- Verify no JavaScript errors preventing state updates
- Check async/await usage in modal function

---

## 📚 File Locations

```
frontend/superadmin/src/
├── services/
│   └── schemeManagementService.js       # API integration
├── components/super/resource_tab/
│   └── CommisonTable.jsx               # Table component
└── pages/super/resources_tab/
    └── SchemeManger.jsx                # Modal integration
```

---

## 🚨 Important Notes

- **Always use `getAllCommissionsByScheme()`** for commission viewing
- **Include loading states** for better UX
- **Handle empty data gracefully** with fallback messages
- **Use proper error boundaries** to prevent UI crashes
- **Test with schemes that have no commissions** to verify empty states

---

**Quick Reference Version**: 1.0  
**Last Updated**: October 3, 2025
