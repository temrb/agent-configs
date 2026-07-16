use port_policy::PortError;

#[test]
fn port_errors_remain_comparable() {
    assert_eq!(PortError::Zero, PortError::Zero);
    assert_eq!(PortError::TooLarge, PortError::TooLarge);
}
