import './Input.css'
export const Input=({label,placeholder,type,value,onChange,className})=>{
    return(
        <>
        <div className='loginInputField'>
        <label className='loginLabel transition-all duration-500 ease text-[24px] md:text-[28px]'>{label}</label>
        <input className={className} 
            type={type} 
            placeholder={placeholder}
            value = {value}
            onChange = {onChange}
        />
        </div>
        </>
    )
}