package com.example.orders;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import com.example.repository.OrderRepository;
import com.example.repository.ProductRepository;
import java.util.List;
import java.util.stream.Collectors;

@Service
public class OrderService {

    @Autowired
    private OrderRepository orderRepository;

    @Autowired
    private ProductRepository productRepository;

    @Transactional
    public List<OrderDto> getOrdersForUser(Long userId) {
        List<Order> orders = orderRepository.findByUserId(userId);
        return orders.stream()
            .map(order -> {
                // N+1: fetches product for every order item
                Product product = productRepository.findById(order.getProductId()).orElse(null);
                return new OrderDto(order, product);
            })
            .collect(Collectors.toList());
    }

    @Transactional
    public List<Order> findActiveOrders() {
        return orderRepository.findByStatus("ACTIVE");
    }

    @Transactional
    private void processInternally(Order order) {
        order.setStatus("PROCESSED");
        orderRepository.save(order);
    }
}
