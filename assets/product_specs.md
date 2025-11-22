# E-Shop Product Specifications

## Product Catalog

### Available Products

1. **Wireless Headphones**
   - Price: $199.99
   - Features: Premium noise-cancelling, 30-hour battery life
   - Stock: Available

2. **Smart Watch**
   - Price: $299.99
   - Features: Fitness tracker, heart rate monitor, GPS
   - Stock: Available

3. **Bluetooth Speaker**
   - Price: $89.99
   - Features: Portable, waterproof, 360-degree sound
   - Stock: Available

## Shopping Cart Functionality

### Add to Cart
- Each product has an "Add to Cart" button
- Clicking the button adds one unit of the product to the cart
- If the product already exists in cart, quantity increases by 1
- Cart displays product name, quantity, unit price, and line total

### Quantity Management
- Users can modify quantity using number input fields
- Setting quantity to 0 removes the item from cart
- Minimum quantity: 0 (removes item)
- No maximum quantity limit

### Price Calculation
- Subtotal = Sum of (product price × quantity) for all items
- Shipping cost added based on selected method
- Discount applied to subtotal before adding shipping
- Final Total = Subtotal - Discount + Shipping

## Discount Code System

### Valid Discount Codes

#### SAVE15
- **Discount**: 15% off subtotal
- **Status**: Active
- **Application**: Applied to cart subtotal before shipping
- **Error Handling**: Shows "15% discount applied!" message in green

#### SAVE20
- **Discount**: 20% off subtotal
- **Status**: Active
- **Application**: Applied to cart subtotal before shipping
- **Error Handling**: Shows "20% discount applied!" message in green

### Invalid Codes
- Any code other than SAVE15 or SAVE20
- Error message: "Invalid discount code" displayed in red
- No discount applied

### Discount Behavior
- Only one discount code can be active at a time
- New code application overwrites previous discount
- Discount shown as separate line item in price breakdown
- Format: "Discount (XX%): -$YY.YY"

## Shipping Options

### Standard Shipping
- **Cost**: Free ($0.00)
- **Delivery Time**: 5-7 business days
- **Default**: Selected by default
- **Radio Button ID**: standard-shipping

### Express Shipping
- **Cost**: $10.00
- **Delivery Time**: 2-3 business days
- **Radio Button ID**: express-shipping

### Shipping Calculation
- Shipping cost added to total after discount
- Changing shipping method immediately updates total
- Shipping cost displayed as separate line if Express selected

## Payment Methods

### Supported Methods

1. **Credit Card**
   - Selected by default
   - Radio button ID: credit-card
   - No additional processing fees

2. **PayPal**
   - Alternative payment option
   - Radio button ID: paypal
   - No additional processing fees

## Form Validation Rules

### Customer Name
- **Field ID**: customer-name
- **Required**: Yes
- **Validation**: Must not be empty
- **Error Message**: "Name is required" (displayed in red)

### Email Address
- **Field ID**: customer-email
- **Required**: Yes
- **Validation**: Must match email format (contains @ and domain)
- **Error Message**: "Please enter a valid email address" (displayed in red)
- **Regex Pattern**: /^[^\s@]+@[^\s@]+\.[^\s@]+$/

### Shipping Address
- **Field ID**: customer-address
- **Required**: Yes
- **Validation**: Must not be empty
- **Error Message**: "Address is required" (displayed in red)

## Checkout Process

### Pay Now Button
- **Button ID**: pay-now-btn
- **Color**: Green background
- **Action**: Validates form and processes payment

### Validation Flow
1. Check if cart is not empty
2. Validate customer name (not empty)
3. Validate email format
4. Validate shipping address (not empty)
5. If all valid → Show "Payment Successful!" message
6. If any validation fails → Display specific error message(s)

### Success State
- **Message**: "Payment Successful!"
- **Display**: Green background, white text, centered
- **Duration**: 3 seconds
- **Element ID**: payment-success

## Business Rules

### Empty Cart Handling
- If cart is empty and user clicks "Pay Now"
- Alert: "Your cart is empty!"
- Payment does not proceed

### Required Fields
- All fields marked with asterisk (*) are mandatory
- Form cannot be submitted until all required fields are valid

### Error Display
- Errors shown inline below respective fields
- Error text displayed in red (#e74c3c)
- Errors hidden by default
- Errors cleared when new validation attempt starts
