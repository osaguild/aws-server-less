<template>
  <div id="counter">
    <p>{{ users[0].id }}, {{ users[0].name }}</p>
    <p>{{ users[1].id }}, {{ users[1].name }}</p>
  </div>
</template>

<script>
import Users from "../data/users"
export default {
  data() {
    return {
      users: Users
    }
  }
}
</script>