module Time {
  fun monthNum (t : Time) {
    `#{t}.getMonth() + 1`
  }

  fun dayNum (t : Time) {
    `#{t}.getDate()`
  }
}
