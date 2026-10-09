import './LoginInput.css'
export const LoginInput=({label,placeholder,type,value,onChange})=>{
    return(
        <>
        <div className='loginInputField'>
        <label className='loginLabel'>{label}</label>
        <input className='loginInput' 
            type={type} 
            placeholder={placeholder}
            value = {value}
            onChange = {onChange}
        />
        </div>
        </>
    )
}