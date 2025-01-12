<template>
   <div class = "w-full"> 
    <div :style="{ 
      backgroundImage: 'url(' + require('@/assets/backgroundImage.png') + ')',
      backgroundSize: 'cover',
      backgroundPosition: 'center',
      height: '100vh'
    }">
    </div>
</div>
  </template>
<script>
export default{
    name:'SectionOne'
}
</script>
