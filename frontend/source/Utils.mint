module Utils {
  fun whenStr (condition : Bool, str : String) {
    if (condition) {
      str
    } else {
      " "
    }
  }

  fun epochToDateString (epoch : Number) {
    `new Date(#{epoch} * 1000).toISOString().slice(0, 10)`
  }
}
