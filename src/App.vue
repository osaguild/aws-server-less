<template>
  <div>
    script worked at {{data.now}}
  </div>
</template>

<script>
import Now from "../data/now.json"
export default {
  data() {
    return {
      data: Now
    }
  }
}
</script>