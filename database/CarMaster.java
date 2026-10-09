

import jakarta.persistence.*;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;
import org.hibernate.annotations.CreationTimestamp;
import org.hibernate.annotations.UpdateTimestamp;

import java.time.LocalDateTime;

@Table(name = "car_master", indexes = {
        @Index(name = "idx_car_master_make", columnList = "make"),
        @Index(name = "idx_car_master_model", columnList = "model")
})
@Data
@NoArgsConstructor
@AllArgsConstructor
@Builder
@Entity
public class CarMaster {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(name = "external_id")
    private String externalId; // Mapped from variant_id

    @Column(nullable = false, length = 50)
    private String make; // Mapped from brand_name

    @Column(nullable = false, length = 100)
    private String model; // Mapped from model_name

    @Column(length = 200)
    private String variant; // Mapped from variant_name

    @Column(length = 50)
    private String segment; // Mapped from segment

    @Column(name = "engine_cc")
    private Integer engineCC; // Mapped from engine_cc

    @Column(name = "fuel_type", length = 50)
    private String fuelType; // Mapped from fuel_type

    @Column(length = 50)
    private String transmission; // Mapped from transmission

    @Column(name = "body_type", length = 50)
    private String bodyType; // Mapped from body_type

    // Seating capacity removed as it is not in the source Excel

    @Column(name = "mileage_arai")
    private Double mileageArai; // Mapped from mileage_arai

    @Column(name = "year_start")
    private Integer yearStart; // Mapped from make_year_start

    @Column(name = "year_end")
    private Integer yearEnd; // Mapped from make_year_end

    @Column(name = "power_hp")
    private String powerHp; // Mapped from power_hp

    @Column(name = "torque_nm")
    private String torqueNm; // Mapped from torque_nm

    @CreationTimestamp
    @Column(name = "created_at", nullable = false, updatable = false)
    private LocalDateTime createdAt;

    @UpdateTimestamp
    @Column(name = "updated_at")
    private LocalDateTime updatedAt;
}
